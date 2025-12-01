import axios, { AxiosError } from "axios";
import { safeParseMessages, safeParseClassifications, safeParseCreateMessageResponse, ErrorResponseSchema } from "./validation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000, // 30 seconds timeout
});

// Response interceptor for validation and error handling
api.interceptors.response.use(
  (response) => {
    // Validate response data based on endpoint
    const url = response.config.url || "";
    
    if (url.includes("/api/messages/") && response.config.method === "get" && !url.includes("/classifications")) {
      // Validate messages list
      const result = safeParseMessages(response.data);
      if (!result.success) {
        console.error("Invalid messages response:", result.error);
        // Don't throw - log error but continue with data
        // This allows the UI to work even if validation fails
        console.warn("Continuing with unvalidated data:", response.data);
      } else {
        response.data = result.data;
      }
    } else if (url.includes("/classifications")) {
      // Validate classifications list
      const result = safeParseClassifications(response.data);
      if (!result.success) {
        console.error("Invalid classifications response:", result.error);
        // Don't throw - log error but continue with data
        // This allows the UI to work even if validation fails
        console.warn("Continuing with unvalidated data:", response.data);
      } else {
        response.data = result.data;
      }
    } else if (url.includes("/api/messages/") && response.config.method === "post") {
      // Validate create message response
      const result = safeParseCreateMessageResponse(response.data);
      if (!result.success) {
        console.error("Invalid create message response:", result.error);
        // Don't throw, but log warning - response might have different structure
        console.warn("Response validation failed, but continuing:", response.data);
      }
    }
    
    return response;
  },
  (error: AxiosError) => {
    // Enhanced error handling
    if (error.response) {
      // Server responded with error status
      const errorData = error.response.data;
      const parsed = ErrorResponseSchema.safeParse(errorData);
      
      if (parsed.success) {
        error.message = parsed.data.detail || error.message;
      }
      
      // Handle rate limiting
      if (error.response.status === 429) {
        error.message = "Rate limit exceeded. Please try again later.";
      }
      
      // Handle network errors
      if (error.code === "ECONNABORTED") {
        error.message = "Request timeout. Please check your connection.";
      }
    } else if (error.request) {
      // Request was made but no response received
      error.message = "No response from server. Please check your connection.";
    }
    
    return Promise.reject(error);
  }
);

// Messages endpoints
export const messagesAPI = {
  createMessage: (client_id: string, content: string) =>
    api.post("/api/messages/", { client_id, content }),
  
  getClientMessages: (client_id: string, limit: number = 50) =>
    api.get(`/api/messages/${client_id}?limit=${limit}`),
  
  getClientClassifications: (client_id: string) =>
    api.get(`/api/messages/${client_id}/classifications`),
};

// Feedback endpoints
export const feedbackAPI = {
  submitFeedback: (data: {
    message_id: string;
    classification_id: string;
    feedback_type: "correct" | "incorrect" | "needs_escalation";
    suggested_scenario?: string;
    comment?: string;
    operator_id: string;
  }) => api.post("/api/feedback/", data),
};

// Health check
export const healthAPI = {
  check: () => api.get("/health"),
};

// WebSocket helper
export const createWebSocketUrl = () => {
  // Replace only the protocol at the start of the URL, not all occurrences of "http"
  // Use regex anchored to start to replace only the protocol scheme
  const baseUrl = API_URL.replace(/^https?/, (protocol) => {
    return protocol === 'https' ? 'wss' : 'ws';
  });
  return baseUrl;
};

// Dialog management API
export const dialogsApi = {
  list: (status?: string) => 
    api.get(`/api/dialogs${status ? `?status=${status}` : ''}`),
  
  get: (clientId: string) => 
    api.get(`/api/dialogs/${clientId}`),
  
  close: (clientId: string) => 
    api.post(`/api/dialogs/${clientId}/close`),
  
  reopen: (clientId: string) => 
    api.post(`/api/dialogs/${clientId}/reopen`),
  
  getStats: (clientId: string) => 
    api.get(`/api/dialogs/${clientId}/stats`),
};
