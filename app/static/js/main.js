// app/static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // Lógica para a Sidebar (se for expandir/contrair)
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }

    // Lógica para preencher informações do usuário logado na sidebar
    const currentUsernameElem = document.getElementById('current-username');
    const currentUserEmailElem = document.getElementById('current-user-email');

    if (currentUsernameElem && currentUserEmailElem) {
        loadUserInfo();
    }

    // Função para carregar informações do usuário
    async function loadUserInfo() {
        try {
            const accessToken = localStorage.getItem('token') || localStorage.getItem('access_token');
            if (!accessToken) {
                currentUsernameElem.textContent = "Visitante";
                currentUserEmailElem.textContent = "";
                return;
            }

            const response = await fetch('/auth/user/profile', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const userData = await response.json();
                currentUsernameElem.textContent = userData.username || "Usuário";
                currentUserEmailElem.textContent = userData.email || "";
            } else {
                // Se falhar ao buscar dados, mostrar placeholders
                currentUsernameElem.textContent = "Product Owner";
                currentUserEmailElem.textContent = "po@empresa.com";
                console.warn('Erro ao carregar informações do usuário:', response.status);
            }
        } catch (error) {
            // Em caso de erro, mostrar placeholders
            currentUsernameElem.textContent = "Product Owner";
            currentUserEmailElem.textContent = "po@empresa.com";
            console.error('Erro ao carregar informações do usuário:', error);
        }
    }
});

// --- FUNÇÃO: fetch autenticado (com token no cabeçalho Authorization) ---
// Esta função será usada para todas as requisições API que precisam de autenticação.
async function authenticatedFetch(url, options = {}) {
    // Pega o token de acesso do localStorage
    console.log('authenticatedFetch - Tentando obter token do localStorage...'); // DEBUG
    // Try both 'token' and 'access_token' for backward compatibility
    const accessToken = localStorage.getItem('token') || localStorage.getItem('access_token'); 
    console.log('authenticatedFetch - Token obtido:', accessToken ? 'Presente' : 'Ausente'); // DEBUG

    // Se não há token no localStorage, redireciona para login e lança um erro.
    if (!accessToken) {
        console.warn('Nenhum token JWT encontrado no localStorage. Redirecionando para login...');
        alert('Sua sessão expirou ou você não está logado. Por favor, faça login novamente.'); // Adicionado alert para o usuário
        window.location.href = '/auth/login_page';
        throw new Error('No JWT token found');
    }
    
    // Adiciona o cabeçalho Authorization com o token JWT
    const headers = {
        ...options.headers, // Mantém outros cabeçalhos existentes
        'Authorization': `Bearer ${accessToken}` // <--- ADICIONA O TOKEN NO CABEÇALHO AQUI
    };

    // 'credentials: "omit"' é usado quando não se espera enviar cookies com a requisição,
    // o que é o caso aqui, já que o token está no cabeçalho e não em um cookie HTTP-only.
    const fetchOptions = {
        ...options,
        headers: headers,
        credentials: 'omit' // Garante que o navegador não tente enviar cookies que possam causar problemas
    };
    
    console.log('authenticatedFetch - URL:', url, 'Options:', fetchOptions); // Log para depuração
    console.log('authenticatedFetch - Cabeçalho Authorization enviado:', headers['Authorization']);
    const response = await fetch(url, fetchOptions);

    console.log('authenticatedFetch - Response Status:', response.status); // Log para depuração

    // Se a resposta for 401 (Unauthorized) ou 403 (Forbidden), geralmente significa que o token
    // JWT expirou ou é inválido. Redireciona para a página de login.
    if (response.status === 401 || response.status === 403) {
        alert('Sessão expirada ou não autorizada. Faça login novamente.');
        localStorage.removeItem('access_token'); // Limpa o token expirado do localStorage
        localStorage.removeItem('user_id');
        window.location.href = '/auth/login_page';
        // Lança um erro para interromper o fluxo da função chamadora
        throw new Error('Authentication expired or unauthorized');
    }

    return response;
}
// --- FIM DA FUNÇÃO: fetch autenticado ---


// Funções para Modais
function openCreateProductModal() {
    document.getElementById('createProductModal').style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Função para Criar Produto (usada pelo dashboard.html)
async function createProduct(event) {
    event.preventDefault(); // Impede o envio padrão do formulário
    
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);
    console.log('createProduct - Tentando criar produto com dados:', data); // DEBUG
    try {
        // Usa a função authenticatedFetch. Ela agora cuida de adicionar o token JWT.
        const response = await authenticatedFetch('/products', { // Sua rota API é /products
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal('createProductModal');
            location.reload(); // Recarrega a página para ver o novo produto
            console.log('Produto criado com sucesso!'); // DEBUG
        } else {
            const errorData = await response.json();
            alert('Erro ao criar produto: ' + (errorData.message || 'Erro desconhecido.'));
            console.error('Erro na resposta da API:', errorData);
            
        }
    } catch (error) {
        console.error('Erro ao criar produto:', error);
        // Lida com erros específicos lançados por authenticatedFetch ou outros erros de rede
        // A mensagem de erro de rede genérica só deve aparecer se não for um erro de autenticação
        if (error.message !== 'Authentication expired or unauthorized' && error.message !== 'No JWT token found') { 
            alert('Ocorreu um erro de rede ou servidor ao tentar criar o produto.');
        }
    }
}

// Função de Logout
function logout() {
    // Remove o token do localStorage
    console.log('Logout - Removendo token do localStorage e redirecionando...'); // DEBUG
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    // Redireciona para a rota de login
    window.location.href = '/auth/login_page';
}

// Função para navegar com token na URL
function navigateWithToken(url) {
    console.log('navigateWithToken called with URL:', url); // DEBUG
    
    try {
        // Try both 'token' and 'access_token' for backward compatibility
        let accessToken = localStorage.getItem('token') || localStorage.getItem('access_token');
        console.log('Token found in localStorage:', accessToken ? 'Yes' : 'No'); // DEBUG
        
        if (accessToken) {
            // Se tem token, adiciona na query string
            const separator = url.includes('?') ? '&' : '?';
            const finalUrl = `${url}${separator}token=${encodeURIComponent(accessToken)}`;
            console.log('Navigating to:', finalUrl); // DEBUG
            window.location.href = finalUrl;
        } else {
            // Se não tem token, vai para login
            console.log('No token found, redirecting to login'); // DEBUG
            alert('Sua sessão expirou ou você não está logado. Por favor, faça login novamente.');
            window.location.href = '/auth/login_page';
        }
    } catch (error) {
        console.error('Error in navigateWithToken:', error);
        alert('Erro ao navegar. Redirecionando para login.');
        window.location.href = '/auth/login_page';
    }
}

// Exemplo de como carregar produtos (se o dashboard precisar de carregamento dinâmico via JS)
// Nota: O dashboard.html atual já espera que 'projects' venha do Flask renderizado no template.
// Esta função seria para um carregamento posterior via JS puro (ex: após um filtro, paginação).
/*
async function loadProducts() {
    try {
        // Usa authenticatedFetch para a requisição GET
        const response = await authenticatedFetch('/products'); // Sua rota API é /products
        if (response.ok) {
            const products = await response.json();
            console.log("Produtos carregados via JS:", products);
            // Aqui você renderizaria os produtos no HTML com JS puro, se necessário
            return products;
        } else {
            const errorData = await response.json();
            console.error('Erro ao carregar produtos:', errorData);
            return [];
        }
    } catch (error) {
        console.error('Erro de rede ou autenticação ao carregar produtos:', error);
        return [];
    }
}
*/

// ============== SISTEMA DE TEMA ESCURO/CLARO ==============

// Função para inicializar o tema
function initializeTheme() {
    // Verificar se há preferência salva, senão usar modo claro por padrão
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme === 'dark') {
        enableDarkMode();
    } else {
        // Por padrão sempre inicia em modo claro
        enableLightMode();
    }
}

// Função para alternar entre temas
function toggleTheme() {
    const isDarkMode = document.documentElement.classList.contains('dark');
    
    if (isDarkMode) {
        enableLightMode();
    } else {
        enableDarkMode();
    }
}

// Função para ativar modo escuro
function enableDarkMode() {
    document.documentElement.classList.add('dark');
    localStorage.setItem('theme', 'dark');
    updateThemeIcon(true);
}

// Função para ativar modo claro
function enableLightMode() {
    document.documentElement.classList.remove('dark');
    localStorage.setItem('theme', 'light');
    updateThemeIcon(false);
}

// Função para atualizar o ícone do toggle
function updateThemeIcon(isDark) {
    const themeIcon = document.querySelector('.fa-moon');
    const toggleButton = document.querySelector('.theme-toggle span');
    
    if (themeIcon) {
        if (isDark) {
            themeIcon.className = 'fas fa-sun text-yellow-400 dark:text-yellow-300';
        } else {
            themeIcon.className = 'fas fa-moon text-gray-600 dark:text-gray-300';
        }
    }
    
    // Animar o toggle
    if (toggleButton) {
        toggleButton.style.transform = isDark ? 'translateX(1rem)' : 'translateX(0.25rem)';
    }
}

// Inicializar tema quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
});

// Tornar as funções globais para uso nos elementos HTML
window.toggleTheme = toggleTheme;
