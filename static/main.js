const loginButton = document.getElementById('login_button');
const loginClose = document.getElementById('login-close');
const loginContent = document.getElementById('login-content');
const doLogin = document.getElementById('do-login');
const signupLink = document.getElementById('signup-link');

// Show modal
loginButton.addEventListener('click', () => {
  loginContent.classList.add('show_login');
});

// Hide modal on close
loginClose.addEventListener('click', () => {
  loginContent.classList.remove('show_login');
});

// Close if clicking outside modal box
loginContent.addEventListener('click', (e) => {
  if (e.target === loginContent) {
    loginContent.classList.remove('show_login');
  }
});

// Login action
doLogin.addEventListener('click', () => {
  const email = document.getElementById('login-email').value;
  const pass = document.getElementById('login-pass').value;

  if (email && pass) {
    alert(`Logging in with Email: ${email}`);
    loginContent.classList.remove('show_login');
  } else {
    alert('Please enter both email and password.');
  }
});

// Sign up action
signupLink.addEventListener('click', (e) => {
  e.preventDefault();
  alert('Redirecting to signup page...');
});
