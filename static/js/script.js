// Small client-side enhancement for the NTCC demonstration.
document.querySelectorAll('input[type="date"]').forEach(el => {
  if (!el.value) el.min = new Date().toISOString().split("T")[0];
});
