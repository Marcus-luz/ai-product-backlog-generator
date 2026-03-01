describe('Fluxo de Autenticação', () => {

  // Antes de todos os testes começarem, garantimos que existe um usuário de teste
  before(() => {
    cy.request({
      method: 'POST',
      url: '/auth/register',
      failOnStatusCode: false, // Se o usuário já existir (erro 409), o teste não quebra
      body: {
        username: 'cypress_user',
        email: 'cypress@teste.com',
        password: 'senha_super_segura'
      }
    })
  })

  beforeEach(() => {
    cy.visit('/auth/login_page')
  })

  it('Deve carregar a página de login corretamente', () => {
    // Agora verifica o texto real que está no seu template
    cy.get('h2').should('contain', 'Bem-vindo de volta!') 
    cy.get('form#loginForm').should('be.visible')
  })

  it('Deve realizar login com sucesso e ir para o Dashboard', () => {
    // Usa o usuário criado no bloco before()
    cy.get('input#username').type('cypress_user')
    cy.get('input#password').type('senha_super_segura')
    
    // Clica no botão e valida se a mensagem de carregamento do seu JS apareceu
    cy.get('button[type="submit"]').click()
    cy.get('button[type="submit"]').should('contain', 'Entrando...')

    // Verifica a mensagem de sucesso disparada pelo seu JS (showMessage)
    cy.get('#message')
      .should('be.visible')
      .and('contain', 'Login bem-sucedido')
      .and('have.class', 'bg-green-100') // Confirma a classe Tailwind de sucesso

    // Como o seu JS tem um setTimeout de 1000ms, damos um tempo maior para o Cypress aguardar a mudança de URL
    cy.url({ timeout: 5000 }).should('include', '/dashboard')
  })

  it('Deve exibir erro com credenciais inválidas', () => {
    cy.get('input#username').type('usuario_fantasma')
    cy.get('input#password').type('senha_errada')
    cy.get('button[type="submit"]').click()

    // Verifica se a div de mensagem aparece com as classes de erro do Tailwind
    cy.get('#message')
      .should('be.visible')
      .and('contain', 'Credenciais inválidas')
      .and('have.class', 'bg-red-100') 
  })

  it('Deve alternar a visibilidade da senha (Ícone do Olho)', () => {
    // Teste bônus: Verificando a interatividade do seu UI (togglePassword)
    cy.get('input#password').type('senha_secreta')
    cy.get('input#password').should('have.attr', 'type', 'password')
    
    cy.get('#passwordToggleIcon').click()
    cy.get('input#password').should('have.attr', 'type', 'text')
    cy.get('#passwordToggleIcon').should('have.class', 'fa-eye-slash')
  })
})