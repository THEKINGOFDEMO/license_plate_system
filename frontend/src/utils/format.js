export function formatConfidence(value) {
  return typeof value === "number" ? value.toFixed(4) : "--";
}

export function formatBbox(bbox) {
  return Array.isArray(bbox) && bbox.length === 4 ? `[${bbox.join(", ")}]` : "--";
}

export function formatStatus(value) {
  if (value === "ok") return "识别成功";
  if (value === "no_detection") return "未检测到";
  if (value === "error") return "错误";
  return value || "--";
}

export function formatDateTime(value) {
  if (!value) {
    return "--";
  }

  const raw = String(value).trim();
  if (!raw) {
    return "--";
  }

  const normalized = raw.replace("T", " ").replace("Z", "");
  const match = normalized.match(
    /^(\d{4}-\d{2}-\d{2})[ ](\d{2}:\d{2}:\d{2})(?:\.\d+)?(?:[+-]\d{2}:\d{2})?$/
  );
  if (match) {
    return `${match[1]} ${match[2]}`;
  }

  const date = new Date(raw);
  if (!Number.isNaN(date.getTime())) {
    const year = date.getFullYear();
    const month = `${date.getMonth() + 1}`.padStart(2, "0");
    const day = `${date.getDate()}`.padStart(2, "0");
    const hours = `${date.getHours()}`.padStart(2, "0");
    const minutes = `${date.getMinutes()}`.padStart(2, "0");
    const seconds = `${date.getSeconds()}`.padStart(2, "0");
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  }

  return normalized;
}
