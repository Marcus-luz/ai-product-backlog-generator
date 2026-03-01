# language: pt
Funcionalidade: Gestão de Produtos
  Como um Product Owner
  Quero poder cadastrar novos produtos
  Para gerenciar meus backlogs

  Contexto:
    Dado que eu tenho um usuario cadastrado e estou logado

  Cenario: Criar um novo produto com sucesso
    Quando eu clico no botão "Novo Produto"
    E preencho o formulario de produto com dados validos
    E clico em "Criar Produto"
    Então eu devo ver o novo produto listado no Dashboard