import {
    deleteNotification,
    fetchNotificationsHistory,
    markNotificationAsRead,
} from "./notificationsApi.js";

const listContainer = document.getElementById("notifications-list");
const unreadBadge = document.getElementById("unread-badge");

function getJwtToken() {
    return localStorage.getItem("jwt_token") || "";
}

function renderNotifications(items) {
    const unreadCount = items.filter((item) => !item.is_read).length;
    unreadBadge.textContent = String(unreadCount);

    if (items.length === 0) {
        listContainer.innerHTML = "<p>Brak powiadomień.</p>";
        return;
    }

    listContainer.innerHTML = "";
    for (const item of items) {
        const card = document.createElement("article");
        card.className = item.is_read ? "item" : "item unread";

        const titleEl = document.createElement("strong");
        titleEl.textContent = item.title;

        const messageEl = document.createElement("p");
        messageEl.textContent = item.message;

        const metaEl = document.createElement("small");
        metaEl.textContent = `${item.type} • ${new Date(item.created_at).toLocaleString("pl-PL")}`;

        const actionsEl = document.createElement("div");
        actionsEl.className = "actions";

        if (!item.is_read) {
            const readBtn = document.createElement("button");
            readBtn.textContent = "Oznacz jako przeczytane";
            readBtn.addEventListener("click", async () => {
                await markNotificationAsRead(item.id, getJwtToken());
                await loadNotifications();
            });
            actionsEl.appendChild(readBtn);
        }

        const deleteBtn = document.createElement("button");
        deleteBtn.textContent = "Usuń";
        deleteBtn.addEventListener("click", async () => {
            await deleteNotification(item.id, getJwtToken());
            await loadNotifications();
        });
        actionsEl.appendChild(deleteBtn);

        card.append(titleEl, messageEl, metaEl, actionsEl);
        listContainer.appendChild(card);
    }
}

async function loadNotifications() {
    const token = getJwtToken();
    try {
        const notifications = await fetchNotificationsHistory(token);
        renderNotifications(notifications);
    } catch (err) {
        listContainer.innerHTML = `<p>Błąd pobierania powiadomień: ${err.message}</p>`;
    }
}

loadNotifications();