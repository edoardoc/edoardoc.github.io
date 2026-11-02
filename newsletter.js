const form = document.querySelector('.subscribe-form');
const email = document.querySelector('#subscriber-email');
const status = document.querySelector('#signup-status');
const submit = form?.querySelector('button[type="submit"]');
const config = window.NITROSEND_SIGNUP;

function showStatus(message, state) {
  status.textContent = message;
  status.hidden = false;
  form.dataset.state = state;
}

if (form && email && status && submit) {
  if (!/^wpkey_live_[a-zA-Z0-9]+$/.test(config?.publicKey || '') || !/^[1-9]\d*$/.test(config?.listId || '')) {
    showStatus('Signup is unavailable right now. Please email apps@500nits.com.', 'error');
  } else {
    submit.disabled = false;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (form.dataset.state === 'submitting' || !form.reportValidity()) return;

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);
      submit.disabled = true;
      form.setAttribute('aria-busy', 'true');
      showStatus('Subscribing…', 'submitting');
      try {
        const response = await fetch('https://api.nitrosend.com/v1/public/contacts', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${config.publicKey}`,
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
          credentials: 'omit',
          signal: controller.signal,
          body: JSON.stringify({
            email: email.value.trim(),
            list_id: config.listId,
            source: 'https://500nits.com/',
            company: form.elements.company.value.trim(),
          }),
        });
        const result = await response.json().catch(() => null);
        if (response.ok && result?.ok === true) {
          form.reset();
          showStatus("You're subscribed.", 'success');
        } else if (response.status === 429) {
          showStatus('Too many attempts. Please try again in a few minutes.', 'error');
        } else if (response.status === 422) {
          showStatus('Please check your email address and try again.', 'error');
        } else {
          showStatus('Could not subscribe. Please try again later or email apps@500nits.com.', 'error');
        }
      } catch {
        showStatus('Could not connect. Check your connection and try again.', 'error');
      } finally {
        clearTimeout(timeout);
        submit.disabled = false;
        form.removeAttribute('aria-busy');
      }
    });
  }
}

for (const link of document.querySelectorAll('a[href="#updates"]')) {
  link.addEventListener('click', (event) => {
    if (!email) return;
    event.preventDefault();
    document.querySelector('#updates').scrollIntoView({ block: 'start' });
    email.focus({ preventScroll: true });
    window.history.replaceState(null, '', '#updates');
  });
}
