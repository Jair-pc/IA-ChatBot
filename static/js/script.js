$(document).ready(function () {

    /* ─── DOM refs ──────────────────────────────────────────────── */
    const $chatOutput   = $('#chat-output');
    const $userInput    = $('#user-input');
    const $sendBtn      = $('#send-button');
    const $stopBtn      = $('#stop-button');
    const $attachBtn    = $('#attach-button');
    const $fileInput    = $('#file-input');
    const $sidebar      = $('#sidebar');
    const $newChatBtn   = $('#newChatBtn');
    const $convList     = $('#conversation-list');
    const $themeBtn     = $('#theme-toggle');
    const $toggleTop    = $('#sidebarToggleTop');
    const $toggleClose  = $('#toggleSidebarBtn');
    const $welcome      = $('#welcome-screen');
    const $body         = $('body');

    let currentChatId   = null;
    let typingInterval  = null;
    let currentReader   = null;

    /* ─── Marked.js + highlight.js ─────────────────────────────── */
    const renderer = new marked.Renderer();

    renderer.code = function (code, lang) {
        const language = lang || 'texto';
        let highlighted;
        try {
            highlighted = lang && hljs.getLanguage(lang)
                ? hljs.highlight(code, { language: lang }).value
                : hljs.highlightAuto(code).value;
        } catch (_) {
            highlighted = $('<div>').text(code).html();
        }
        const uid = 'code-' + Math.random().toString(36).slice(2, 8);
        return `<div class="code-block">
            <div class="code-header">
                <span class="code-lang">${language}</span>
                <button class="copy-btn" data-uid="${uid}">
                    <i class="fas fa-copy"></i> Copiar
                </button>
            </div>
            <pre><code id="${uid}" class="hljs">${highlighted}</code></pre>
        </div>`;
    };

    marked.setOptions({ renderer, breaks: true });

    /* Copy handler */
    $(document).on('click', '.copy-btn', function () {
        const $btn = $(this);
        const uid  = $btn.data('uid');
        const text = document.getElementById(uid)?.textContent || '';
        navigator.clipboard.writeText(text).then(() => {
            $btn.addClass('copied').html('<i class="fas fa-check"></i> Copiado!');
            setTimeout(() => $btn.removeClass('copied').html('<i class="fas fa-copy"></i> Copiar'), 2000);
        });
    });

    /* ─── Theme ─────────────────────────────────────────────────── */
    const HLJS_DARK  = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css';
    const HLJS_LIGHT = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css';

    function applyTheme(isLight) {
        $body.toggleClass('light-mode', isLight);
        $themeBtn.find('i').toggleClass('fa-sun', !isLight).toggleClass('fa-moon', isLight);
        $('#hljs-theme').attr('href', isLight ? HLJS_LIGHT : HLJS_DARK);
    }

    applyTheme(localStorage.getItem('theme') === 'light');

    $themeBtn.on('click', function () {
        const isLight = !$body.hasClass('light-mode');
        applyTheme(isLight);
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
    });

    /* ─── Sidebar ───────────────────────────────────────────────── */
    function openSidebar() {
        $sidebar.removeClass('collapsed');
        $toggleTop.hide();
        localStorage.setItem('sidebar', 'open');
        if (window.innerWidth <= 768) {
            $('<div class="sidebar-overlay active" id="sb-overlay"></div>')
                .appendTo('body')
                .on('click', closeSidebar);
        }
    }

    function closeSidebar() {
        $sidebar.addClass('collapsed');
        $toggleTop.show();
        localStorage.setItem('sidebar', 'closed');
        $('#sb-overlay').remove();
    }

    if (localStorage.getItem('sidebar') === 'closed') {
        closeSidebar();
    } else {
        $toggleTop.hide();
    }

    $toggleClose.on('click', closeSidebar);
    $toggleTop.on('click', openSidebar);

    /* ─── Textarea auto-resize ──────────────────────────────────── */
    $userInput.on('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        $sendBtn.prop('disabled', !$(this).val().trim());
    });

    $userInput.on('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if ($userInput.val().trim() || attachedFile) sendMessage();
        }
    });

    /* ─── File attach ───────────────────────────────────────────── */
    const FILE_ICONS = {
        pdf: '📄', txt: '📝', doc: '📝', docx: '📝',
        xlsx: '📊', xls: '📊', csv: '📊',
        png: '🖼️', jpg: '🖼️', jpeg: '🖼️', gif: '🖼️', webp: '🖼️', bmp: '🖼️',
    };

    let attachedFile = null;

    $attachBtn.on('click', () => $fileInput.trigger('click'));

    $fileInput.on('change', function () {
        const file = this.files?.[0];
        if (!file) return;
        attachedFile = file;

        const ext  = file.name.split('.').pop().toLowerCase();
        const icon = FILE_ICONS[ext] || '📎';
        const $chip = $('#attachmentChip');

        // Limpa conteúdo anterior (exceto o botão remover)
        $chip.find('.chip-icon, .chip-info, img.chip-img').remove();

        if (['png','jpg','jpeg','gif','webp','bmp'].includes(ext)) {
            const reader = new FileReader();
            reader.onloadend = () => {
                $chip.prepend(`<img class="chip-img" src="${reader.result}" alt="preview">`);
            };
            reader.readAsDataURL(file);
        } else {
            $chip.prepend(`
                <span class="chip-icon">${icon}</span>
                <div class="chip-info">
                    <span class="chip-name">${file.name}</span>
                    <span class="chip-type">${ext.toUpperCase()}</span>
                </div>
            `);
        }

        $('#attachmentRow').show();
        $sendBtn.prop('disabled', false);
        this.value = '';
    });

    $('#removeAttach').on('click', function () {
        attachedFile = null;
        $('#attachmentRow').hide();
        $('#attachmentChip').find('.chip-icon, .chip-info, img.chip-img').remove();
        $fileInput.val('');
    });

    /* ─── Messages ──────────────────────────────────────────────── */
    function scrollToBottom() {
        const el = document.getElementById('messages-scroll');
        if (el) el.scrollTop = el.scrollHeight;
    }

    const usernameInitial = (window.UCB_USERNAME || 'U')[0].toUpperCase();

    function escapeHtml(text) {
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function appendMessageRaw(sender, htmlContent) {
        $welcome.hide();
        const html = `<div class="message user-message">
            <div class="msg-avatar">${usernameInitial}</div>
            <div class="msg-bubble"><div class="msg-content">${htmlContent}</div></div>
        </div>`;
        $chatOutput.append(html);
        scrollToBottom();
    }

    function appendMessage(text, sender, isTemporary = false) {
        $welcome.hide();

        let html;
        if (sender === 'user') {
            html = `<div class="message user-message">
                <div class="msg-avatar">${usernameInitial}</div>
                <div class="msg-bubble"><div class="msg-content">${escapeHtml(text)}</div></div>
            </div>`;
        } else if (isTemporary) {
            html = `<div class="message assistant-message loading">
                <div class="msg-avatar"><img src="../static/img/Logo.png" alt="UCBvet"></div>
                <div class="msg-bubble">
                    <div class="typing-dots"><span></span><span></span><span></span></div>
                </div>
            </div>`;
        } else {
            const parsed = marked.parse(String(text));
            html = `<div class="message assistant-message">
                <div class="msg-avatar"><img src="../static/img/Logo.png" alt="UCBvet"></div>
                <div class="msg-bubble"><div class="msg-content">${parsed}</div></div>
            </div>`;
        }

        $chatOutput.append(html);
        scrollToBottom();
    }

    /* ─── Send / Stop ───────────────────────────────────────────── */
    async function getBotResponse(userMessage, file) {
        // Cria bolha de loading
        appendMessage('', 'assistant', true);
        const $loadingMsg = $('.message.loading').last();

        try {
            let res;
            if (file) {
                const fd = new FormData();
                fd.append('message', userMessage);
                fd.append('file', file);
                res = await fetch(`/stream_response/${currentChatId}`, { method: 'POST', body: fd });
            } else {
                res = await fetch(`/stream_response/${currentChatId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: userMessage }),
                });
            }
            if (!res.ok) throw new Error('Erro na resposta');

            // Substitui loading por bolha vazia para receber o streaming
            $loadingMsg.removeClass('loading').find('.msg-bubble').html('<div class="msg-content"></div>');
            const $msgContent = $loadingMsg.find('.msg-content');

            const reader = res.body.getReader();
            currentReader = reader;
            const decoder = new TextDecoder();
            let buffer   = '';
            let fullText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    let evt;
                    try { evt = JSON.parse(line.slice(6)); } catch { continue; }

                    if (evt.content) {
                        fullText += evt.content;
                        $msgContent.html(marked.parse(fullText));
                        scrollToBottom();
                    }
                    if (evt.error) {
                        $msgContent.text('Erro: ' + evt.error);
                    }
                    if (evt.done && evt.new_title) {
                        $(`.conversation[data-id="${currentChatId}"] .conv-title`).text(evt.new_title);
                    }
                }
            }

        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error(err);
                $loadingMsg.remove();
                appendMessage('Ocorreu um erro ao obter a resposta.', 'assistant');
            }
        } finally {
            currentReader = null;
            $stopBtn.hide();
            $sendBtn.show().prop('disabled', !$userInput.val().trim());
        }
    }

    function sendMessage() {
        const message = $userInput.val().trim();
        const file    = attachedFile;

        if (!message && !file) return;

        // Monta label da mensagem do usuário
        if (file) {
            const ext  = file.name.split('.').pop().toLowerCase();
            const icon = FILE_ICONS[ext] || '📎';
            const fileLabel = `<div class="msg-file-chip">${icon} <span>${file.name}</span></div>`;
            const textLabel = message ? `<div>${escapeHtml(message)}</div>` : '';
            appendMessageRaw('user', fileLabel + textLabel);
        } else {
            appendMessage(message, 'user');
        }

        // Limpa input e attachment
        $userInput.val('').css('height', 'auto');
        attachedFile = null;
        $('#attachmentRow').hide();
        $('#attachmentChip').find('.chip-icon, .chip-info, img.chip-img').remove();
        $fileInput.val('');

        $sendBtn.prop('disabled', true).hide();
        $stopBtn.show();

        if (!currentChatId) {
            startNewConversation().then(() => getBotResponse(message, file));
        } else {
            getBotResponse(message, file);
        }
    }

    $sendBtn.on('click', sendMessage);

    $stopBtn.on('click', function () {
        if (currentReader) { currentReader.cancel(); currentReader = null; }
        clearInterval(typingInterval);
        $('.loading').remove();
        $stopBtn.hide();
        $sendBtn.show().prop('disabled', !$userInput.val().trim());
    });

    /* ─── Conversations ─────────────────────────────────────────── */
    function groupByDate(conversations) {
        const now  = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const yest  = new Date(today); yest.setDate(yest.getDate() - 1);
        const w7    = new Date(today); w7.setDate(w7.getDate() - 7);

        const groups = { 'Hoje': [], 'Ontem': [], 'Últimos 7 dias': [], 'Mais antigos': [] };
        conversations.forEach(c => {
            const d   = new Date(c.timestamp);
            const day = new Date(d.getFullYear(), d.getMonth(), d.getDate());
            if      (day >= today) groups['Hoje'].push(c);
            else if (day >= yest)  groups['Ontem'].push(c);
            else if (day >= w7)    groups['Últimos 7 dias'].push(c);
            else                   groups['Mais antigos'].push(c);
        });
        return groups;
    }

    async function loadConversations() {
        try {
            const res = await fetch('/get_conversations');
            if (!res.ok) return;
            const list = await res.json();
            $convList.empty();

            const groups = groupByDate(list);
            Object.entries(groups).forEach(([label, items]) => {
                if (!items.length) return;
                $convList.append(`<span class="time-label">${label}</span>`);
                items.forEach(conv => {
                    const $c = $(`
                        <div class="conversation${conv.id === currentChatId ? ' active' : ''}" data-id="${conv.id}">
                            <span class="conv-title editable" contenteditable="false">${conv.title || 'Sem título'}</span>
                            <div class="conv-actions">
                                <button class="conv-btn edit-conv-btn" title="Editar"><i class="fas fa-pencil-alt"></i></button>
                                <button class="conv-btn del-conv-btn"  title="Excluir"><i class="fas fa-trash-alt"></i></button>
                            </div>
                        </div>`);
                    $convList.append($c);
                });
            });
        } catch (e) { console.error(e); }
    }

    /* Click conversation */
    $convList.on('click', '.conversation', function (e) {
        if ($(e.target).closest('.conv-actions').length) return;
        const id = $(this).data('id');
        currentChatId = id;
        $('.conversation').removeClass('active');
        $(this).addClass('active');
        loadChatMessages(id);
        updateExportBtn();
    });

    /* Delete */
    $convList.on('click', '.del-conv-btn', async function (e) {
        e.stopPropagation();
        const $c  = $(this).closest('.conversation');
        const id  = $c.data('id');
        try {
            const res = await fetch(`/delete_chat/${id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
            if (res.ok) {
                if (currentChatId === id) {
                    currentChatId = null;
                    $chatOutput.empty();
                    $welcome.show();
                }
                loadConversations();
            }
        } catch (e) { console.error(e); }
    });

    /* Edit title */
    $convList.on('click', '.edit-conv-btn', function (e) {
        e.stopPropagation();
        const $t = $(this).closest('.conversation').find('.conv-title');
        $t.attr('contenteditable', 'true').addClass('editing').focus();
        const range = document.createRange();
        range.selectNodeContents($t[0]);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    });

    $convList.on('keydown', '.conv-title', function (e) {
        if (e.key === 'Enter')  { e.preventDefault(); $(this).blur(); }
        if (e.key === 'Escape') { $(this).attr('contenteditable', 'false').removeClass('editing'); loadConversations(); }
    });

    $convList.on('blur', '.conv-title', async function () {
        const $t = $(this);
        if (!$t.hasClass('editing')) return;
        $t.attr('contenteditable', 'false').removeClass('editing');
        const id    = $t.closest('.conversation').data('id');
        const title = $t.text().trim() || 'Sem título';
        try {
            await fetch(`/update_chat_title/${id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title }),
            });
            loadConversations();
        } catch (e) { console.error(e); }
    });

    async function loadChatMessages(chatId) {
        try {
            const res = await fetch(`/get_messages/${chatId}`);
            if (!res.ok) return;
            const msgs = await res.json();
            $chatOutput.empty();
            $welcome.hide();
            msgs.forEach(m => {
                if (m.usuario)  appendMessage(m.usuario,  'user');
                if (m.servidor) appendMessage(m.servidor, 'assistant');
            });
        } catch (e) { console.error(e); }
    }

    async function startNewConversation() {
        try {
            const res = await fetch('/add_chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: 'Nova Conversa' }),
            });
            if (res.ok) {
                const data = await res.json();
                currentChatId = data.chat_id;
                $chatOutput.empty();
                $welcome.hide();
                loadConversations();
                updateExportBtn();
            }
        } catch (e) { console.error(e); }
    }

    $newChatBtn.on('click', function () {
        clearInterval(typingInterval);
        $('.loading').remove();
        $stopBtn.hide();
        $sendBtn.show().prop('disabled', !$userInput.val().trim());
        currentChatId = null;
        $chatOutput.empty();
        $welcome.show();
        $('.conversation').removeClass('active');
        updateExportBtn();
    });

    /* ─── Exportar conversa ─────────────────────────────────────── */
    $('#exportChatBtn').on('click', function () {
        if (currentChatId) window.open(`/export_chat/${currentChatId}`, '_blank');
    });

    // Mostrar/ocultar botão de exportar conforme chat ativo
    function updateExportBtn() {
        currentChatId ? $('#exportChatBtn').show() : $('#exportChatBtn').hide();
    }

    /* ─── Modal troca de senha ───────────────────────────────────── */
    function openPwdModal() {
        $('#pwdCurrent, #pwdNew, #pwdConfirm').val('');
        $('#pwdMsg').text('').removeClass('error');
        $('#pwdModalOverlay').addClass('open');
        setTimeout(() => $('#pwdCurrent').focus(), 100);
    }
    function closePwdModal() {
        $('#pwdModalOverlay').removeClass('open');
    }

    $('#change-password-btn').on('click', openPwdModal);
    $('#pwdModalClose, #pwdCancel').on('click', closePwdModal);
    $('#pwdModalOverlay').on('click', function (e) {
        if ($(e.target).is('#pwdModalOverlay')) closePwdModal();
    });

    $('#pwdConfirmBtn').on('click', async function () {
        const current = $('#pwdCurrent').val();
        const newPwd  = $('#pwdNew').val();
        const confirm = $('#pwdConfirm').val();
        const $msg    = $('#pwdMsg');

        if (!current || !newPwd || !confirm) {
            $msg.addClass('error').text('Preencha todos os campos.');
            return;
        }
        if (newPwd !== confirm) {
            $msg.addClass('error').text('As senhas não coincidem.');
            return;
        }
        if (newPwd.length < 4) {
            $msg.addClass('error').text('A nova senha deve ter pelo menos 4 caracteres.');
            return;
        }

        $(this).prop('disabled', true).text('Alterando…');
        try {
            const res = await fetch('/change_password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ current_password: current, new_password: newPwd }),
            });
            const data = await res.json();
            if (data.error) {
                $msg.addClass('error').removeClass('success').text(data.error);
            } else {
                $msg.removeClass('error').css('color', 'var(--accent)').text(data.message);
                setTimeout(closePwdModal, 1500);
            }
        } catch {
            $msg.addClass('error').text('Erro de conexão.');
        } finally {
            $(this).prop('disabled', false).text('Alterar senha');
        }
    });

    /* ─── Logout ────────────────────────────────────────────────── */
    $('#logout-button').on('click', async function () {
        try { await $.ajax({ url: '/logout', method: 'GET' }); } catch (_) {}
        window.location.href = '/';
    });

    /* ─── Init ──────────────────────────────────────────────────── */
    loadConversations();
});
