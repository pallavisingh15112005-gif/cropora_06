"""Auto-close the sidebar drawer after a page is picked from it."""

import streamlit as st

_HTML = """<!doctype html>
<html><body><script>
(function () {
  var doc;
  try { doc = window.parent.document; } catch (e) { return; }
  if (doc.__croporaDrawerHook) return;
  doc.__croporaDrawerHook = true;

  function collapse() {
    var btn = doc.querySelector(
      '[data-testid="stSidebar"] button[aria-label="Collapse sidebar"], ' +
      '[data-testid="stSidebarCollapseButton"] button'
    );
    if (!btn) return false;
    btn.click();
    return true;
  }

  doc.addEventListener("click", function (ev) {
    var link = ev.target && ev.target.closest
      ? ev.target.closest('[data-testid="stSidebar"] a[href]')
      : null;
    if (!link) return;
    var tries = 0;
    (function attempt() {
      tries += 1;
      if (collapse() || tries > 15) return;
      setTimeout(attempt, 120);
    })();
  }, true);
})();
</script></body></html>
"""


def inject_autoclose() -> None:
    st.iframe(_HTML, height=1)
