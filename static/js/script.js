$(document).ready(function() {
    const $chatOutput = $('#chat-output');
    const $userInput = $('#user-input');
    const $sendButton = $('#send-button');
    const $stopButton = $('#stop-button');
    const $attachButton = $('#attach-button');
    const $fileInput = $('#file-input');
    const $sidebar = $('.sidebar');
    const $newConversationBtn = $('.new-conversation-btn');
    const $toggleSidebarBtn = $('#toggleSidebarBtn');
    const $conversationList = $('#conversation-list');
    const $themeToggle = $('#theme-toggle');
    const $body = $('body');
    let currentConversationId = null;
    let typingInterval = null;

    // Função para adicionar uma mensagem no chat
    function appendMessage(text, sender, isTemporary = false) {
        const messageHtml = `
            <div class="message ${sender === 'user' ? 'user-message' : 'assistant-message'} ${isTemporary ? 'loading' : ''}">
                ${isTemporary && sender === 'assistant' ? '<div class="loading-indicator"></div>' : ''}
                <div class="message-content">${text}</div>
            </div>
        `;
        $chatOutput.append(messageHtml);
        $chatOutput.scrollTop($chatOutput[0].scrollHeight);
    }

    // Função para enviar uma mensagem
    function sendMessage() {
        const message = $userInput.val();
        if (message.trim() !== '') {
            appendMessage(message, 'user');
            $userInput.val('');
            $stopButton.show();
            $sendButton.hide();
            if (currentConversationId === null) {
                startNewConversation().then(() => {
                    getBotResponse(message);
                });
            } else {
                getBotResponse(message);
            }
        }
    }

    // Função para obter resposta do bot usando a API Gemini
    async function getBotResponse(userMessage) {
        appendMessage('Escrevendo...', 'assistant', true);

        try {
            const response = await fetch(`/get_response/${currentConversationId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage }),
            });

            if (!response.ok) {
                throw new Error('Erro ao obter resposta do bot');
            }

            const data = await response.json();
            const botMessage = data.response;

            $('.loading').remove();
            simulateTyping(botMessage, 'assistant');
        } catch (error) {
            console.error('Erro:', error);
            appendMessage('Erro ao obter resposta do bot.', 'assistant');
        }
    }

    // Função para obter resposta do bot usando a nova rota para consultas SQL genéricas
    async function getBotResponseGeneric(userMessage) {
        appendMessage('Escrevendo...', 'assistant', true);

        try {
            const response = await fetch(`/get_response`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ mensagem: userMessage }),
            });

            if (!response.ok) {
                throw new Error('Erro ao obter resposta do bot');
            }

            const data = await response.json();
            const botMessage = data.resposta;

            $('.loading').remove();
            simulateTyping(botMessage, 'assistant');
        } catch (error) {
            console.error('Erro:', error);
            appendMessage('Erro ao obter resposta do bot.', 'assistant');
        }
    }

    // Função para simular a digitação gradual do bot
    function simulateTyping(text, sender) {
        let index = 0;
        const messageHtml = `
            <div class="message ${sender === 'user' ? 'user-message' : 'assistant-message'}">
                <div class="message-content"></div>
            </div>
        `;
        $chatOutput.append(messageHtml);
        const $messageContent = $chatOutput.find('.message-content').last();

        typingInterval = setInterval(() => {
            if (index < text.length) {
                $messageContent.append(text[index]);
                index++;
                $chatOutput.scrollTop($chatOutput[0].scrollHeight);
            } else {
                clearInterval(typingInterval);
                $stopButton.hide();
                $sendButton.show();
                loadConversations();
            }
        }, 50);
    }

    // Evento de clique para interromper a resposta do bot
    $stopButton.on('click', function() {
        clearInterval(typingInterval);
        $('.loading').remove();
        $stopButton.hide();
        $sendButton.show();
    });

    // Função para carregar mensagens do chat
    async function loadChatMessages(chatId) {
        try {
            const response = await fetch(`/get_messages/${chatId}`);
            if (response.ok) {
                const messages = await response.json();
                $chatOutput.empty();
                messages.forEach(msg => {
                    appendMessage(msg.usuario, 'user');
                    appendMessage(msg.servidor, 'assistant');
                });
            } else {
                console.error('Erro ao carregar mensagens:', response.statusText);
            }
        } catch (error) {
            console.error('Erro ao carregar mensagens:', error);
        }
    }

    // Função para iniciar nova conversa
    async function startNewConversation() {
        try {
            const response = await fetch('/add_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title: 'Nova Conversa' }),
            });
            if (response.ok) {
                const newChat = await response.json();
                currentConversationId = newChat.chat_id;
                $chatOutput.empty();
                $stopButton.hide();
                $sendButton.show();
                appendMessage('Nova conversa iniciada.', 'assistant');
                return Promise.resolve();
            } else {
                console.error('Erro ao iniciar nova conversa:', response.statusText);
                return Promise.reject();
            }
        } catch (error) {
            console.error('Erro ao iniciar nova conversa:', error);
            return Promise.reject();
        }
    }

    // Evento de clique para abrir o seletor de arquivos
    $attachButton.on('click', function() {
        $fileInput.click();
    });

    // Eventos de clique e tecla para enviar mensagem
    $sendButton.on('click', sendMessage);
    $userInput.on('keypress', function(e) {
        if (e.which == 13) {
            sendMessage();
        }
    });

    // Evento de clique para iniciar nova conversa
    $newConversationBtn.on('click', function() {
        if ($stopButton.is(':visible')) {
            clearTimeout(botResponseTimeout);
            clearInterval(typingInterval);
            $('.loading').remove();
            $stopButton.hide();
            $sendButton.show();
        }
        startNewConversation();
    });

    // Função para carregar conversas
    async function loadConversations() {
        try {
            const response = await fetch('/get_conversations');
            if (response.ok) {
                const conversations = await response.json();
                $conversationList.empty();
                conversations.forEach(conv => {
                    const convHtml = `
                        <div class="conversation" data-id="${conv.id}">
                            <div class="conversation-header">
                                <span class="conversation-date">${new Date(conv.timestamp).toLocaleString()}</span>
                                <div class="conversation-actions">
                                    <button class="action-btn edit-conversation-btn" title="Editar Conversa">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="action-btn delete-conversation-btn" title="Deletar Conversa">
                                        <i class="fas fa-trash-alt"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="conversation-content">
                                <div class="editable message assistant-message" contenteditable="false">
                                    ${conv.title}
                                </div>
                            </div>
                        </div>
                    `;
                    $conversationList.append(convHtml);
                });
            } else {
                console.error('Erro ao carregar conversas:', response.statusText);
            }
        } catch (error) {
            console.error('Erro ao carregar conversas:', error);
        }
    }

    // Evento de clique para selecionar uma conversa existente
    $conversationList.on('click', '.conversation', function() {
        const chatId = $(this).data('id');
        currentConversationId = chatId;
        loadChatMessages(chatId);
    });

    // Evento de clique para deletar uma conversa
    $conversationList.on('click', '.delete-conversation-btn', async function(e) {
        e.stopPropagation();
        const chatId = $(this).closest('.conversation').data('id');
        try {
            const response = await fetch(`/delete_chat/${chatId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            if (response.ok) {
                loadConversations();
                if (currentConversationId === chatId) {
                    currentConversationId = null;
                    $chatOutput.empty();
                }
            } else {
                console.error('Erro ao deletar conversa:', response.statusText);
            }
        } catch (error) {
            console.error('Erro ao deletar conversa:', error);
        }
    });

    // Evento de clique para editar uma conversa
    $conversationList.on('click', '.edit-conversation-btn', function(e) {
        e.stopPropagation();
        const $editable = $(this).closest('.conversation').find('.editable');
        $editable.attr('contenteditable', 'true').addClass('editing').focus();
    });

    // Evento de perda de foco para salvar a edição de uma conversa
    $conversationList.on('blur', '.editable', async function() {
        const $this = $(this);
        const chatId = $this.closest('.conversation').data('id');
        const newTitle = $this.text();
        try {
            await fetch(`/update_chat_title/${chatId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title: newTitle }),
            });
            $this.attr('contenteditable', 'false').removeClass('editing');
            loadConversations();
        } catch (error) {
            console.error('Erro ao atualizar título da conversa:', error);
        }
    });

    // Alternar o tema
    $themeToggle.on('click', function() {
        $body.toggleClass('dark-mode');
        if ($body.hasClass('dark-mode')) {
            $themeToggle.find('i').removeClass('fa-lightbulb').addClass('fa-lightbulb');
            localStorage.setItem('theme', 'dark');
        } else {
            $themeToggle.find('i').removeClass('fa-lightbulb').addClass('fa-lightbulb');
            localStorage.setItem('theme', 'light');
        }
    });

    // Carregar o tema armazenado no localStorage
    if (localStorage.getItem('theme') === 'dark') {
        $body.addClass('dark-mode');
        $themeToggle.find('i').removeClass('fa-lightbulb').addClass('fa-lightbulb');
    }

    // Evento de clique para alternar a visibilidade da barra lateral
    $toggleSidebarBtn.on('click', function() {
        $sidebar.toggleClass('closed');
        const iconClass = $sidebar.hasClass('closed') ? 'fa-chevron-right' : 'fa-chevron-left';
        $(this).find('i').attr('class', `fas ${iconClass}`);
    });

    // Carregar conversas ao iniciar
    loadConversations();
    
    // logout.
    $('#logout-button').on('click', async function() {
        try {
            const response = await $.ajax({
                url: '/logout',
                method: 'GET'
            });

            if (response) {
                window.location.href = '/';  // Redireciona para a página de login
            } else {
                console.error('Erro ao fazer logout:', response.statusText);
            }
        } catch (error) {
            console.error('Erro ao fazer logout:', error);
        }
    });
});
