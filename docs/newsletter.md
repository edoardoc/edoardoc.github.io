# 500nits product updates

The homepage has one prominent, labeled email form. Until a newsletter account is connected, it opens an email draft to apps@500nits.com. The visitor must send that message; submitting the form alone does not subscribe anyone. Requests and removals must be handled manually. No subscriber data is stored in the repository or browser.

## Recommended hosted setup

Buttondown supports a plain HTML form, so no backend, API key, third-party script, or iframe is necessary. Its published pricing on 2026-10-31 includes the first 100 subscribers free. Verify pricing when opening the account.

1. Create a newsletter in an account you own at https://buttondown.com/ and verify your sender email. Choose the newsletter username there; do not assume that `500nits` is available or belongs to you.
2. Copy the exact form action from the account's embedding settings. Confirm it is the newsletter you control. Buttondown documents the shape as `https://buttondown.com/api/emails/embed-subscribe/YOUR-BUTTONDOWN-USERNAME`.
3. In index.html, replace the form's mailto action with that verified HTTPS action, retain `method="post"`, remove `enctype="text/plain"`, and add `<input type="hidden" name="embed" value="1" />`.
4. Change the button to `Subscribe` and replace `#signup-note` with accurate confirmation, unsubscribe, and provider privacy information for the configured newsletter. Keep a visible label and required email input. Add the provider privacy link before collecting addresses there.
5. Submit natively to Buttondown. Do not use fetch: the response may require CAPTCHA or further validation. newsletter.js already leaves HTTPS actions to the browser.
6. Test with an email address you control: verify the confirmation flow, subscriber record, and unsubscribe flow. Then run the SEO audit, commit, push, and verify the live form.

Sources: https://docs.buttondown.com/building-your-subscriber-base and https://buttondown.com/pricing.

The account-specific action URL is the only missing integration detail. Never publish a guessed endpoint, expose an API key, or claim that opening a draft has added a subscriber.
