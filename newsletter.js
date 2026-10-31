const form = document.querySelector('.subscribe-form');
const email = document.querySelector('#subscriber-email');
const status = document.querySelector('#signup-status');

// A hosted HTTPS form can replace the mailto action without changing this script.
if (form && email && status && new URL(form.action).protocol === 'mailto:') {
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const address = email.value.trim();
    const subject = 'Subscribe to 500nits updates';
    const body = `Hi Eddy,\n\nPlease add ${address} to your list for occasional 500nits product updates.\n\nI can reply to ask you to remove me from the list.\n`;
    const draft = `mailto:apps@500nits.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    status.replaceChildren(
      document.createTextNode('Send the message in your email app to request updates. If it didn’t open, '),
    );
    const retry = document.createElement('a');
    retry.href = draft;
    retry.textContent = 'open the email draft';
    status.append(retry, document.createTextNode(' or email apps@500nits.com.'));
    status.hidden = false;
    window.location.href = draft;
  });
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
