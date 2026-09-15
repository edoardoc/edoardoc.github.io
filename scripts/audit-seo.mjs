#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(scriptDirectory, "..");
const registryPath = path.join(repositoryRoot, ".agents", "sites.json");
const registry = JSON.parse(fs.readFileSync(registryPath, "utf8"));
const errors = [];
const warnings = [];

const normalizeUrl = (value) => {
  const url = new URL(value);
  url.hash = "";
  return url.href;
};

const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const findTag = (html, tagName, attributeName, attributeValue) => {
  const tags = html.match(new RegExp(`<${tagName}\\b[^>]*>`, "gi")) ?? [];
  const expected = new RegExp(
    `\\b${escapeRegExp(attributeName)}\\s*=\\s*(["'])${escapeRegExp(attributeValue)}\\1`,
    "i",
  );
  return tags.find((tag) => expected.test(tag));
};

const attribute = (tag, name) => {
  if (!tag) return null;
  const match = tag.match(new RegExp(`\\b${escapeRegExp(name)}\\s*=\\s*(["'])(.*?)\\1`, "i"));
  return match?.[2]?.trim() ?? null;
};

const readFile = (filePath, label) => {
  if (!fs.existsSync(filePath)) {
    errors.push(`${label}: missing ${path.relative(repositoryRoot, filePath)}`);
    return null;
  }
  return fs.readFileSync(filePath, "utf8");
};

const walkHtml = (directory, excludedDirectories) => {
  const files = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const absolute = path.join(directory, entry.name);
    if (excludedDirectories.has(absolute) || entry.name === ".git" || entry.name === "uploads") continue;
    if (entry.isDirectory()) files.push(...walkHtml(absolute, excludedDirectories));
    if (entry.isFile() && entry.name.endsWith(".html")) files.push(absolute);
  }
  return files;
};

const sourceRoots = registry.sites.map((site) => path.resolve(repositoryRoot, site.sourcePath));

for (const site of registry.sites) {
  const siteRoot = path.resolve(repositoryRoot, site.sourcePath);
  const baseUrl = new URL(site.baseUrl);
  const label = `${site.id} (${baseUrl.origin})`;
  const excludedDirectories = new Set(
    sourceRoots.filter(
      (candidate) => candidate !== siteRoot && candidate.startsWith(`${siteRoot}${path.sep}`),
    ),
  );

  if (!fs.existsSync(siteRoot)) {
    errors.push(`${label}: source directory is missing: ${site.sourcePath}`);
    continue;
  }

  if (site.cname) {
    const cnamePath = path.join(siteRoot, site.cname);
    const cname = readFile(cnamePath, label)?.trim();
    if (cname && cname !== baseUrl.hostname) {
      errors.push(`${label}: CNAME is ${cname}, expected ${baseUrl.hostname}`);
    }
  }

  const sitemapUrl = new URL(site.sitemap, baseUrl).href;
  const robots = readFile(path.join(siteRoot, site.robots), label);
  if (robots) {
    if (!/^User-agent:\s*\*\s*$/im.test(robots)) {
      errors.push(`${label}: robots.txt has no User-agent: * group`);
    }
    if (!new RegExp(`^Sitemap:\\s*${escapeRegExp(sitemapUrl)}\\s*$`, "im").test(robots)) {
      errors.push(`${label}: robots.txt must name ${sitemapUrl}`);
    }
  }

  const sitemap = readFile(path.join(siteRoot, site.sitemap), label);
  if (!sitemap) continue;
  const locations = [...sitemap.matchAll(/<loc>\s*([^<]+?)\s*<\/loc>/gi)].map(
    (match) => match[1],
  );
  if (locations.length === 0) errors.push(`${label}: sitemap has no <loc> entries`);
  if (new Set(locations).size !== locations.length) {
    errors.push(`${label}: sitemap contains duplicate URLs`);
  }

  const sitemapFiles = new Set();
  for (const location of locations) {
    let pageUrl;
    try {
      pageUrl = new URL(location);
    } catch {
      errors.push(`${label}: invalid sitemap URL ${location}`);
      continue;
    }

    if (pageUrl.protocol !== "https:") errors.push(`${label}: sitemap URL is not HTTPS: ${location}`);
    if (pageUrl.origin !== baseUrl.origin) errors.push(`${label}: cross-origin sitemap URL: ${location}`);
    if (pageUrl.search || pageUrl.hash) {
      errors.push(`${label}: sitemap URL contains a query or fragment: ${location}`);
    }

    let relativePage = decodeURIComponent(pageUrl.pathname).replace(/^\/+/, "");
    if (!relativePage || relativePage.endsWith("/")) relativePage += "index.html";
    const pagePath = path.resolve(siteRoot, relativePage);
    if (!pagePath.startsWith(`${siteRoot}${path.sep}`) && pagePath !== siteRoot) {
      errors.push(`${label}: sitemap path escapes the site root: ${location}`);
      continue;
    }
    sitemapFiles.add(pagePath);
    const html = readFile(pagePath, `${site.id}: ${location}`);
    if (!html) continue;

    const title = html
      .match(/<title\b[^>]*>([\s\S]*?)<\/title>/i)?.[1]
      ?.replace(/<[^>]+>/g, "")
      .replace(/\s+/g, " ")
      .trim();
    const description = attribute(findTag(html, "meta", "name", "description"), "content");
    const canonical = attribute(findTag(html, "link", "rel", "canonical"), "href");
    const robotsMeta = attribute(findTag(html, "meta", "name", "robots"), "content");
    const headings = html.match(/<h1\b[^>]*>/gi) ?? [];

    if (!/<html\b[^>]*\blang\s*=/i.test(html)) {
      errors.push(`${site.id}: ${location} has no html lang attribute`);
    }
    if (!title) errors.push(`${site.id}: ${location} has no non-empty title`);
    if (!description) errors.push(`${site.id}: ${location} has no meta description`);
    if (!canonical) {
      errors.push(`${site.id}: ${location} has no canonical link`);
    } else {
      try {
        if (normalizeUrl(canonical) !== normalizeUrl(location)) {
          errors.push(`${site.id}: ${location} canonical is ${canonical}`);
        }
      } catch {
        errors.push(`${site.id}: ${location} has an invalid canonical: ${canonical}`);
      }
    }
    if (!robotsMeta || !/\bindex\b/i.test(robotsMeta) || /\bnoindex\b/i.test(robotsMeta)) {
      errors.push(`${site.id}: ${location} must explicitly be indexable`);
    }
    if (headings.length !== 1) {
      errors.push(`${site.id}: ${location} has ${headings.length} h1 elements; expected 1`);
    }

    for (const match of html.matchAll(/500nits/gi)) {
      if (match[0] !== "500nits") {
        errors.push(`${site.id}: ${location} contains non-lowercase brand text: ${match[0]}`);
      }
    }
  }

  for (const htmlPath of walkHtml(siteRoot, excludedDirectories)) {
    if (sitemapFiles.has(htmlPath)) continue;
    const html = fs.readFileSync(htmlPath, "utf8");
    const robotsMeta = attribute(findTag(html, "meta", "name", "robots"), "content");
    if (!robotsMeta || !/\bnoindex\b/i.test(robotsMeta)) {
      errors.push(
        `${site.id}: ${path.relative(siteRoot, htmlPath)} is outside the sitemap and must explicitly be noindex`,
      );
    }
  }

  const homepage = readFile(path.join(siteRoot, "index.html"), label);
  if (homepage) {
    for (const property of ["og:type", "og:title", "og:description", "og:url", "og:image"]) {
      if (!attribute(findTag(homepage, "meta", "property", property), "content")) {
        errors.push(`${label}: homepage has no ${property}`);
      }
    }
    if (!attribute(findTag(homepage, "meta", "name", "twitter:card"), "content")) {
      errors.push(`${label}: homepage has no twitter:card`);
    }
    if (!/type\s*=\s*(["'])application\/ld\+json\1/i.test(homepage)) {
      warnings.push(`${label}: homepage has no JSON-LD; add it only when accurate and useful`);
    }
  }
}

for (const error of errors) console.error(`ERROR: ${error}`);
for (const warning of warnings) console.warn(`WARN: ${warning}`);

console.log(`Audited ${registry.sites.length} sites: ${errors.length} error(s), ${warnings.length} warning(s).`);
if (errors.length > 0) process.exitCode = 1;
