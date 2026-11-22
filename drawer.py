"""Auto-close the sidebar drawer after a page is picked from it."""

import streamlit as st

_HTML = """<!doctype html>
<html><body><script>
(function () {
  var doc;
  try { doc = window.parent.document; } catch (e) { return; }
  if (doc.__croporaDrawerHook) return;
  doc.__croporaDrawerHook = true;
  doc.__croporaHookInfo = { clicks: 0, collapses: 0 };

  function sidebarWidth() {
    var sb = doc.querySelector('[data-testid="stSidebar"]');
    return sb ? sb.getBoundingClientRect().width : 0;
  }

  function collapse() {
    var btn = doc.querySelector(
      '[data-testid="stSidebar"] button[aria-label="Collapse sidebar"], ' +
      '[data-testid="stSidebarCollapseButton"] button'
    );
    if (!btn) return false;
    btn.click();
    doc.__croporaHookInfo.collapses += 1;
    return true;
  }

  // Streamlit reruns after navigation and can reopen the drawer, so keep
  // closing it for a few seconds instead of collapsing only once.
  function watch(ms) {
    if (doc.__croporaWatch) return;
    var end = Date.now() + ms;
    var lastClick = 0;
    var timer = setInterval(function () {
      if (Date.now() > end) {
        clearInterval(timer);
        doc.__croporaWatch = 0;
        return;
      }
      if (sidebarWidth() > 120 && Date.now() - lastClick > 700) {
        lastClick = Date.now();
        collapse();
      }
    }, 150);
    doc.__croporaWatch = timer;
  }

  function onNav(ev) {
    var link = ev.target && ev.target.closest
      ? ev.target.closest('[data-testid="stSidebar"] a[href]')
      : null;
    if (!link) return;
    doc.__croporaHookInfo.clicks += 1;
    watch(6000);
  }

  doc.addEventListener("pointerdown", onNav, true);
  doc.addEventListener("click", onNav, true);
})();
</script></body></html>
"""


def inject_autoclose() -> None:
    st.iframe(_HTML, height=1)
