export const LOGIN_FLAG_KEY = "lpr_logged_in";
export const LOGIN_USER_KEY = "lpr_login_user";
export const DEMO_USERNAME = "admin";
export const DEMO_PASSWORD = "123456";

export function isLoggedIn() {
  return localStorage.getItem(LOGIN_FLAG_KEY) === "true";
}

export function login(username) {
  localStorage.setItem(LOGIN_FLAG_KEY, "true");
  localStorage.setItem(LOGIN_USER_KEY, username || DEMO_USERNAME);
}

export function logout() {
  localStorage.removeItem(LOGIN_FLAG_KEY);
  localStorage.removeItem(LOGIN_USER_KEY);
}

export function getLoginUser() {
  return localStorage.getItem(LOGIN_USER_KEY) || DEMO_USERNAME;
}
