(function () {
  try {
    var savedTheme = localStorage.getItem("findmyspot-theme");
    var preferredDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    var initialTheme = savedTheme || (preferredDark ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", initialTheme);
  } catch (e) {
    document.documentElement.setAttribute("data-theme", "light");
  }
})();
