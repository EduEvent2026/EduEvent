const API_BASE_URL = "http://localhost:8007";

function authHeaders(token) {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
    };
}

export async function fetchNotificationsHistory(token) {
    const response = await fetch(`${API_BASE_URL}/notifications/history`, {
        method: "GET",
        headers: authHeaders(token),
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
}

export async function markNotificationAsRead(notificationId, token) {
    const response = await fetch(`${API_BASE_URL}/notifications/${notificationId}/read`, {
        method: "PATCH",
        headers: authHeaders(token),
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
}

export async function deleteNotification(notificationId, token) {
    const response = await fetch(`${API_BASE_URL}/notifications/${notificationId}`, {
        method: "DELETE",
        headers: authHeaders(token),
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
}