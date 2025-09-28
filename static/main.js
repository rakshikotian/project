// ===== Get Elements =====
const loginModal = document.getElementById("login-content");
const signupModal = document.getElementById("signup-content");

const loginBtn = document.getElementById("login_button");   // navbar login button
const signupBtn = document.getElementById("signup_button"); // navbar signup button (if you have one)

const loginClose = document.getElementById("login-close");
const signupClose = document.getElementById("signup-close");

// ===== Open / Close Functions =====
function openLogin() {
   document.querySelectorAll(".arrow").forEach(a => a.classList.add("blur"));
  signupModal.classList.remove("show_signup"); // hide signup if open
  loginModal.classList.add("show_login");
}

function closeLogin() {
   document.querySelectorAll(".arrow").forEach(a => a.classList.remove("blur"));
  loginModal.classList.remove("show_login");
}

function openSignup() {
  document.querySelectorAll(".arrow").forEach(a => a.classList.add("blur"));
  loginModal.classList.remove("show_login"); // hide login if open
  signupModal.classList.add("show_signup");
}

function closeSignup() {
  document.querySelectorAll(".arrow").forEach(a => a.classList.remove("blur"));
  signupModal.classList.remove("show_signup");
}

// ===== Event Listeners =====
// Navbar buttons
if (loginBtn) {
  loginBtn.addEventListener("click", openLogin);
}
if (signupBtn) {
  signupBtn.addEventListener("click", openSignup);
}

// Close buttons
loginClose.addEventListener("click", closeLogin);
signupClose.addEventListener("click", closeSignup);

// Close if clicking outside modal box
window.addEventListener("click", (e) => {
  if (e.target === loginModal) closeLogin();
  if (e.target === signupModal) closeSignup();
});

// ===== Removed form handling via JS =====
// The forms will be submitted to PHP scripts directly,
// so you no longer need to handle form submissions here.
