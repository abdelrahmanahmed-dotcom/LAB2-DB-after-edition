

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const todoForm = document.getElementById("todoForm");
const titleInput = document.getElementById("title");
const todoList = document.getElementById("todoList");
const message = document.getElementById("message");

async function apiRequest(url, method = "GET", data = null) {
    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json"
        }
    };

    if (data !== null) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || "Something went wrong");
    }

    return result;
}

if (loginForm) {
    loginForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        message.textContent = "";

        try {
            await apiRequest("/api/login", "POST", {
                email: document.getElementById("email").value,
                password: document.getElementById("password").value
            });

            window.location.href = "/todo-test.html";
        } catch (error) {
            message.textContent = error.message;
        }
    });
}

if (registerForm) {
    registerForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        message.textContent = "";

        try {
            await apiRequest("/api/register", "POST", {
                name: document.getElementById("name").value,
                email: document.getElementById("email").value,
                password: document.getElementById("password").value
            });

            window.location.href = "/todo-test.html";
        } catch (error) {
            message.textContent = error.message;
        }
    });
}

function createTodoElement(todo) {
    const li = document.createElement("li");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = todo.is_done;

    const taskText = document.createElement("span");
    taskText.textContent = todo.title;

    function updateText() {
        taskText.style.textDecoration = checkbox.checked
            ? "line-through"
            : "none";
    }

    updateText();

    checkbox.addEventListener("change", async function() {
        try {
            await apiRequest("/api/todos/" + todo.id, "PUT", {
                is_done: checkbox.checked
            });
            updateText();
        } catch (error) {
            checkbox.checked = !checkbox.checked;
            alert(error.message);
        }
    });

    const deleteButton = document.createElement("button");
    deleteButton.textContent = "Delete";
    deleteButton.type = "button";

    deleteButton.addEventListener("click", async function() {
        try {
            await apiRequest("/api/todos/" + todo.id, "DELETE");
            li.remove();
        } catch (error) {
            alert(error.message);
        }
    });

    li.appendChild(checkbox);
    li.appendChild(taskText);
    li.appendChild(deleteButton);

    return li;
}

async function loadTodos() {
    try {
        const todos = await apiRequest("/api/todos");

        todoList.innerHTML = "";

        for (let i = 0; i < todos.length; i++) {
            todoList.appendChild(createTodoElement(todos[i]));
        }
    } catch (error) {
        if (error.message === "Authentication required") {
            window.location.href = "/login.html";
        } else {
            alert(error.message);
        }
    }
}

if (todoForm) {
    todoForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const taskTitle = titleInput.value.trim();

        if (taskTitle === "") {
            return;
        }

        try {
            const todo = await apiRequest("/api/todos", "POST", {
                title: taskTitle
            });

            todoList.prepend(createTodoElement(todo));
            titleInput.value = "";
        } catch (error) {
            alert(error.message);
        }
    });

    loadTodos();
}

const logoutLink = document.getElementById("logoutLink");

if (logoutLink) {
    logoutLink.addEventListener("click", async function(event) {
        event.preventDefault();

        try {
            await apiRequest("/api/logout", "POST");
            window.location.href = "/login.html";
        } catch (error) {
            alert(error.message);
        }
    });
}
