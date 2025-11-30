export const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    (process.env.NODE_ENV === "production"
        ? "https://pokepedai-backend-api-405120827006.us-east1.run.app"
        : "http://localhost:8080");
