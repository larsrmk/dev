// DOM Elemente
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const toRegister = document.getElementById('to-register');
const toLogin = document.getElementById('to-login');

// Fehlerfelder
const loginError = document.getElementById('login-error');
const usernameError = document.getElementById('username-error');
const emailError = document.getElementById('email-error');
const passwordError = document.getElementById('password-error');

// Umschalten zwischen Login & Registrierung
toRegister.addEventListener('click', () => {
  loginForm.style.display = 'none';
  registerForm.style.display = 'block';
  clearErrors();
});

toLogin.addEventListener('click', () => {
  registerForm.style.display = 'none';
  loginForm.style.display = 'block';
  clearErrors();
});

function clearErrors() {
  loginError.textContent = '';
  usernameError.textContent = '';
  emailError.textContent = '';
  passwordError.textContent = '';
}

// --- LOGIN ---
loginForm.addEventListener('submit', async e => {
  e.preventDefault();
  clearErrors();

  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email, password})
    });

    const data = await res.json();

    if (res.ok) {
      window.location.href = '/welcome.html';  // weiße Seite
    } else {
      loginError.textContent = data.message;
    }
  } catch (err) {
    loginError.textContent = 'Serverfehler, bitte später erneut versuchen.';
  }
});

// --- REGISTRIERUNG ---
registerForm.addEventListener('submit', async e => {
  e.preventDefault();
  clearErrors();

  const username = document.getElementById('register-username').value.trim();
  const email = document.getElementById('register-email').value.trim();
  const password = document.getElementById('register-password').value;
  const password2 = document.getElementById('register-password2').value;

  if (password !== password2) {
    passwordError.textContent = 'Passwörter stimmen nicht überein.';
    return;
  }

  try {
    const res = await fetch('/api/register', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, email, password})
    });

    const data = await res.json();

    if (res.ok) {
      window.location.href = '/welcome.html';  // weiße Seite
    } else {
      if(data.field === 'username') {
        usernameError.textContent = data.message;
      } else if(data.field === 'email') {
        emailError.textContent = data.message;
      } else {
        passwordError.textContent = data.message;
      }
    }
  } catch (err) {
    passwordError.textContent = 'Serverfehler, bitte später erneut versuchen.';
  }
});
