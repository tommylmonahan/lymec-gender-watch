const STORAGE_KEY = "lymec-gender-watch-v1";
const THEME_KEY = "lymec-gender-watch-theme";
const MAX_VISIBLE_ENTRIES = 8;

const elements = {
  firstTime: document.querySelector("#firstTimeCheckbox"),
  headerTotal: document.querySelector("#headerTotal"),
  totalCount: document.querySelector("#totalCount"),
  totalFirstTime: document.querySelector("#totalFirstTime"),
  manCount: document.querySelector("#manCount"),
  manFirstTime: document.querySelector("#manFirstTime"),
  womanCount: document.querySelector("#womanCount"),
  womanFirstTime: document.querySelector("#womanFirstTime"),
  manPercent: document.querySelector("#manPercent"),
  womanPercent: document.querySelector("#womanPercent"),
  manBar: document.querySelector("#manBar"),
  womanBar: document.querySelector("#womanBar"),
  historyList: document.querySelector("#historyList"),
  emptyState: document.querySelector("#emptyState"),
  undoButton: document.querySelector("#undoButton"),
  exportButton: document.querySelector("#exportButton"),
  resetButton: document.querySelector("#resetButton"),
  resetDialog: document.querySelector("#resetDialog"),
  confirmResetButton: document.querySelector("#confirmResetButton"),
  themeButton: document.querySelector("#themeButton"),
  toast: document.querySelector("#toast"),
  backupStatus: document.querySelector("#backupStatus"),
  backupStatusText: document.querySelector("#backupStatusText"),
};

let entries = loadEntries();
let toastTimer;
let serverAvailable = false;
let backupQueue = Promise.resolve();

function loadEntries() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (!Array.isArray(stored)) return [];
    return stored.filter(
      (entry) =>
        entry &&
        (entry.gender === "Man" || entry.gender === "Woman") &&
        typeof entry.firstTime === "boolean" &&
        typeof entry.timestamp === "string",
    );
  } catch {
    return [];
  }
}

function saveEntries() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch (error) {
    console.error("Browser storage failed:", error);
    setBackupStatus("error", "Browser copy failed - disk backup may still be safe");
  }
}

function setBackupStatus(state, message) {
  elements.backupStatus.dataset.state = state;
  elements.backupStatusText.textContent = message;
}

async function initializeBackup() {
  if (location.protocol !== "http:" && location.protocol !== "https:") {
    setBackupStatus("error", "Browser-only mode - use start.bat for Excel backup");
    return;
  }

  setBackupStatus("connecting", "Connecting to local backup...");
  try {
    const response = await fetch("/api/records", { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Could not read the local backup.");

    serverAvailable = true;
    if (payload.initialized) {
      if (entries.length > payload.entries.length) {
        await syncBackup("restore");
      } else {
        entries = payload.entries;
        saveEntries();
        render();
        setBackupStatus("saved", "Excel backup active - all records saved");
      }
    } else if (entries.length > 0) {
      await syncBackup("restore");
    } else {
      setBackupStatus("saved", "Excel backup active - ready to record");
    }
  } catch (error) {
    console.error("Backup connection failed:", error);
    setBackupStatus("error", "Disk backup unavailable - browser copy is active");
  }
}

function syncBackup(action = "update") {
  if (!serverAvailable) return Promise.resolve();

  const snapshot = entries.map((entry) => ({ ...entry }));
  backupQueue = backupQueue
    .catch(() => undefined)
    .then(async () => {
      setBackupStatus("saving", "Updating Excel backup...");
      const response = await fetch("/api/records", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entries: snapshot, action }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "The disk backup could not be updated.");
      setBackupStatus("saved", "Excel backup active - all records saved");
    })
    .catch((error) => {
      console.error("Backup write failed:", error);
      setBackupStatus("error", error.message || "Backup failed - browser copy is safe");
    });

  return backupQueue;
}

function count(gender, firstTimeOnly = false) {
  return entries.filter(
    (entry) => entry.gender === gender && (!firstTimeOnly || entry.firstTime),
  ).length;
}

function formatTime(timestamp) {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(timestamp));
}

function render() {
  const total = entries.length;
  const men = count("Man");
  const women = count("Woman");
  const firstTimers = entries.filter((entry) => entry.firstTime).length;
  const menFirstTime = count("Man", true);
  const womenFirstTime = count("Woman", true);
  const menShare = total ? Math.round((men / total) * 100) : 0;
  const womenShare = total ? 100 - menShare : 0;

  elements.headerTotal.textContent = total;
  elements.totalCount.textContent = total;
  elements.totalFirstTime.textContent = `${firstTimers} first-time ${firstTimers === 1 ? "delegate" : "delegates"}`;
  elements.manCount.textContent = men;
  elements.manFirstTime.textContent = `${menFirstTime} first-time`;
  elements.womanCount.textContent = women;
  elements.womanFirstTime.textContent = `${womenFirstTime} first-time`;
  elements.manPercent.textContent = `${menShare}%`;
  elements.womanPercent.textContent = `${womenShare}%`;
  elements.manBar.style.width = `${menShare}%`;
  elements.womanBar.style.width = `${womenShare}%`;

  const hasEntries = total > 0;
  elements.undoButton.disabled = !hasEntries;
  elements.exportButton.disabled = !hasEntries;
  elements.resetButton.disabled = !hasEntries;
  elements.emptyState.hidden = hasEntries;

  elements.historyList.replaceChildren(
    ...entries
      .slice(-MAX_VISIBLE_ENTRIES)
      .reverse()
      .map((entry, visibleIndex) => createHistoryItem(entry, total - visibleIndex)),
  );
}

function createHistoryItem(entry, number) {
  const item = document.createElement("li");
  item.className = "history-item";

  const entryNumber = document.createElement("span");
  entryNumber.className = "history-number";
  entryNumber.textContent = `#${number}`;

  const person = document.createElement("div");
  person.className = "history-person";
  const gender = document.createElement("strong");
  gender.textContent = entry.gender;
  person.append(gender);

  if (entry.firstTime) {
    const badge = document.createElement("span");
    badge.className = "first-time-badge";
    badge.textContent = "First-time";
    person.append(badge);
  }

  const time = document.createElement("time");
  time.className = "history-time";
  time.dateTime = entry.timestamp;
  time.textContent = formatTime(entry.timestamp);

  item.append(entryNumber, person, time);
  return item;
}

function recordEntry(gender) {
  const isFirstTime = elements.firstTime.checked;
  entries.push({
    id: globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`,
    gender,
    firstTime: isFirstTime,
    timestamp: new Date().toISOString(),
  });
  saveEntries();
  render();
  syncBackup("record");
  showToast(`${gender}${isFirstTime ? " · first-time delegate" : ""} recorded`);
}

function undoLast() {
  const removed = entries.pop();
  if (!removed) return;
  saveEntries();
  render();
  syncBackup("undo");
  showToast(`Last ${removed.gender.toLowerCase()} entry removed`);
}

function resetSession() {
  entries = [];
  elements.firstTime.checked = false;
  saveEntries();
  render();
  syncBackup("reset");
  showToast("Session reset and previous data archived");
}

function exportCsv() {
  const header = ["Entry", "Gender", "First-time delegate", "Date", "Time"];
  const rows = entries.map((entry, index) => {
    const date = new Date(entry.timestamp);
    return [
      index + 1,
      entry.gender,
      entry.firstTime ? "Yes" : "No",
      date.toLocaleDateString(),
      date.toLocaleTimeString(),
    ];
  });
  const csv = [header, ...rows]
    .map((row) => row.map(csvCell).join(","))
    .join("\r\n");
  const blob = new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  const dateLabel = new Date().toISOString().slice(0, 10);
  link.href = URL.createObjectURL(blob);
  link.download = `lymec-gender-watch-${dateLabel}.csv`;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
  showToast("CSV exported");
}

function csvCell(value) {
  const text = String(value).replaceAll('"', '""');
  return `"${text}"`;
}

function showToast(message) {
  clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.add("visible");
  toastTimer = setTimeout(() => elements.toast.classList.remove("visible"), 1800);
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem(THEME_KEY, theme);
  const nextTheme = theme === "dark" ? "light" : "dark";
  elements.themeButton.setAttribute("aria-label", `Use ${nextTheme} theme`);
}

function initializeTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  const preferred = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  setTheme(saved === "light" || saved === "dark" ? saved : preferred);
}

document.querySelectorAll("[data-gender]").forEach((button) => {
  button.addEventListener("click", () => recordEntry(button.dataset.gender));
});

elements.undoButton.addEventListener("click", undoLast);
elements.exportButton.addEventListener("click", exportCsv);
elements.resetButton.addEventListener("click", () => elements.resetDialog.showModal());
elements.confirmResetButton.addEventListener("click", resetSession);
elements.themeButton.addEventListener("click", () => {
  const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  setTheme(nextTheme);
});

document.addEventListener("keydown", (event) => {
  if (event.ctrlKey || event.metaKey || event.altKey || elements.resetDialog.open) return;
  const activeTag = document.activeElement?.tagName;
  if (activeTag === "INPUT" || activeTag === "BUTTON") return;

  if (event.key.toLowerCase() === "m") recordEntry("Man");
  if (event.key.toLowerCase() === "w") recordEntry("Woman");
  if (event.key.toLowerCase() === "f") {
    elements.firstTime.checked = !elements.firstTime.checked;
    showToast(`First-time ${elements.firstTime.checked ? "on" : "off"}`);
  }
});

initializeTheme();
render();
initializeBackup();
