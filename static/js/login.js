document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("login-form");
  
    loginForm.addEventListener("submit", async function (event) {
      event.preventDefault(); // Evita que o formulário seja enviado de forma padrão
  
      // Obtenção dos valores dos campos de entrada
      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;
  
      try {
        const response = await fetch("/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ username, password }),
        });
  
        if (response.ok) {
          window.location.href = "/home"; // Redireciona para a rota home se o login for bem-sucedido
        } else {
          const errorMessage = await response.text();
          alert(errorMessage); // Exibe a mensagem de erro retornada pelo Flask
        }
      } catch (error) {
        console.error("Erro ao processar a solicitação:", error);
        alert("Ocorreu um erro ao processar a solicitação. Por favor, tente novamente mais tarde.");
      }
    });
  });
  