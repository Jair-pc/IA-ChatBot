document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("cadastro-form");

    form.addEventListener("submit", async function (event) {
        event.preventDefault(); // Evita o comportamento padrão de envio do formulário

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirm-password").value;

        // Verifica se as senhas coincidem
        if (password !== confirmPassword) {
            alert("As senhas não coincidem.");
            return;
        }

        try {
            const response = await fetch("/cadastrar", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();
            if (response.ok) {
                alert(data.message);
                form.reset();
                window.location.href = "/"; // Redireciona para a página inicial após o cadastro
            } else {
                alert(data.error);
            }
        } catch (error) {
            console.error("Erro ao processar a solicitação:", error);
            alert("Ocorreu um erro ao processar a solicitação. Por favor, tente novamente mais tarde.");
        }
    });
});
