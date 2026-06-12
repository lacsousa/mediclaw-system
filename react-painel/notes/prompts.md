1:

OK, voce tem a atual modelagem do banco de dados, quero fazer alterações no comportamento da aplicação
Hoje o usuário que loga na aplicação é o user ( usuário ) que teoricamente é o médico que está atendendo pacientes
Quero que o usuário que loga na aplicação continue da forma que está, mas que a cada chat aberto, após a digitação dos dados ( nome, idade, peso, atividades físicas, dados de sono, nutrição) sejam atreladas a uma nova entidade chamada paciente (patient) que hoje não existe na aplicaçao.
Então assim que o paciente responder o nome, o paciente será incluído no banco de dados e os próximos dados serão atribuídos a este paciente: conversas, dados.
Para o Banco de dados um user(médico) pode ter vários pacientes em cada conversa de chat. Para o frontend, podemos já mostrar na barra lateral a conversa salva com o nome do paciente atual
Vamos fazer essa nova especificação de forma interativa, você agindo como um Engenheiro de Software especialista em engenharia de software, requisitos, ux, banco de dados e vamos manter e alterar as specs que já existem no estilo BMAD
