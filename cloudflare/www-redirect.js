export default {
  fetch(request) {
    const url = new URL(request.url);
    url.protocol = "https:";
    url.hostname = "500nits.com";

    const lastSegment = url.pathname.split("/").pop();
    if (url.pathname !== "/" && !url.pathname.endsWith("/") && !lastSegment.includes(".")) {
      url.pathname += "/";
    }

    return Response.redirect(url.toString(), 301);
  },
};
