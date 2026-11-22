// Small wrapper around fetch for talking to the FastAPI backend.
// Errors are turned into ApiError objects with a general message and per-field messages.

export class ApiError extends Error {
  constructor(status, message, fieldErrors = {}) {
    super(message);
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

let onUnauthorized = () => {};
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

export async function apiRequest(path, { method = "GET", body, token } = {}) {
  const headers = {};
  const isForm = typeof FormData !== "undefined" && body instanceof FormData;
  if (body !== undefined && !isForm) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(path, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "Can't reach the server. Check that the backend is running and try again.");
  }

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    if (response.status === 401 && token) onUnauthorized();
    const fieldErrors = {};
    for (const err of data?.errors ?? []) fieldErrors[err.field] = err.message;
    let message = typeof data?.detail === "string" ? data.detail : "Something went wrong. Please try again.";
    // Validation errors that aren't tied to a visible field are shown in the main message.
    const general = (data?.errors ?? []).filter((e) => e.field === "request").map((e) => e.message);
    if (general.length) message = general.join(" ");
    throw new ApiError(response.status, message, fieldErrors);
  }
  return data;
}

export const APPLICATION_STATUSES = ["Saved", "Applied", "Interview", "Offer", "Rejected", "Withdrawn"];

export const REQUEST_TYPES = {
  resume_review: "Resume review",
  interview_practice: "Interview practice",
  career_guidance: "Career guidance",
};

export const REQUEST_STATUS_LABELS = {
  pending: "Pending",
  accepted: "Accepted",
  in_progress: "In progress",
  completed: "Completed",
  declined: "Declined",
  cancelled: "Cancelled",
};

export const KIND_LABELS = {
  internship: "Internship",
  job: "Job",
  event: "Event",
  announcement: "Announcement",
};
