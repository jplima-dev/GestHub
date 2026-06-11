const form = document.querySelector("#registerForm");
const toast = document.querySelector("#toast");

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3200);
}

async function csrfToken() {
  const response = await fetch("/api/auth/csrf");
  const data = await response.json();
  return data.csrf_token;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(form).entries());

  if (data.password !== data.confirm_password) {
    showToast("A confirmação de senha deve ser igual à senha.");
    return;
  }

  try {
    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-csrf-token": await csrfToken(),
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Não foi possível criar a conta.");
    }

    const result = await response.json();
    localStorage.setItem("condoflow.token", result.access_token);
    localStorage.setItem("condoflow.user", JSON.stringify(result.user));
    window.location.href = "/";
  } catch (error) {
    showToast(error.message);
  }
});

