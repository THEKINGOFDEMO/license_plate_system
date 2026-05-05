import request from "./request";

export function fetchHealth() {
  return request.get("/api/health/");
}

export function getStats() {
  return request.get("/api/stats/");
}

export function recognizeImage(file) {
  const formData = new FormData();
  formData.append("image", file);
  return request.post("/api/recognize/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
}

export function fetchRecords(params = {}) {
  return request.get("/api/records/", { params });
}

export function resolveApiBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
}
