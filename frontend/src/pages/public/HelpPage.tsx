import { Link } from "react-router-dom";
import { Card } from "../../components/ui";

const sections = [
  { id: "paciente", title: "Para quem precisa de atendimento", intro: "Comece pelo que você precisa fazer agora.", items: [
    ["Preciso de atendimento", "Responda às perguntas sobre o que está acontecendo. Ao terminar, você verá uma orientação sobre o tipo de unidade a procurar. Isso não é um diagnóstico.", "/atendimento"],
    ["Ver unidades de saúde", "Veja endereços, serviços e a espera aproximada. Use os filtros para buscar por nome, cidade ou tipo de unidade. O mapa ajuda a localizar cada uma.", "/unidades"],
    ["Entrar na fila online", "Depois das perguntas, escolha uma UPA. Se houver horários disponíveis, escolha um intervalo de chegada, como 10h às 10h30. Você recebe um número de pedido, chamado protocolo. Também pode enviar o pedido sem escolher horário.", "/atendimento"],
    ["Acompanhar meu pedido", "Digite seu protocolo para ver a posição na fila, a previsão de chegada e as novidades do atendimento. A página se atualiza sozinha. Confira antes de sair e mostre o número à recepção quando chegar.", "/acompanhar"],
    ["Avisar que estou a caminho", "Se você já está indo para um hospital, envie um aviso contando o que aconteceu e em quanto tempo pretende chegar. A equipe poderá confirmar que recebeu. Esse aviso não chama ambulância, não reserva leito e não coloca você na fila online.", "/paciente/pre-alerta"],
    ["Minha conta e meus pedidos", "Encontre seus pedidos anteriores e as mensagens sobre eles. Para guardar os pedidos na sua conta, entre ou faça seu cadastro.", "/paciente/conta"],
    ["Emergência", "Use esta página para acessar a ligação para o SAMU 192 e as orientações de emergência. Não espere um horário da fila para buscar socorro.", "/emergencia"],
  ]},
  { id: "upa", title: "Para a equipe da UPA", intro: "Acompanhe os pedidos desde o envio até o fim do atendimento.", items: [
    ["Resumo do dia", "Veja quantos pedidos chegaram, quem está esperando e quantos atendimentos terminaram. Os gráficos ajudam a acompanhar o movimento.", "/upa"],
    ["Pedidos de atendimento", "Abra os detalhes, confirme que recebeu o pedido e registre a chegada quando a pessoa estiver na unidade. Depois, registre o início e o fim do atendimento. Se precisar cancelar, informe o motivo.", "/upa/solicitacoes"],
    ["Fila online", "Veja a ordem dos pedidos e os horários de chegada escolhidos. Use “Chamar próximo” para continuar. Quem escolheu horário precisa ter a chegada registrada antes de ser chamado.", "/upa/fila"],
    ["Avisos de chegada", "Leia os avisos de quem informou estar a caminho. Confirme o recebimento e atualize a situação conforme a pessoa chega e o aviso é encerrado.", "/upa/alertas"],
    ["Equipe e estrutura", "Informe quantos profissionais e salas estão disponíveis e quantas pessoas podem ser recebidas. Esses dados ajudam a calcular a espera mostrada ao paciente.", "/upa/capacidade"],
  ]},
  { id: "hospital", title: "Para a equipe do hospital", intro: "Saiba quem avisou que está a caminho e acompanhe cada aviso.", items: [
    ["Resumo do dia", "Veja os avisos recebidos, quantas pessoas estão a caminho e quanto tempo a equipe leva para confirmar o recebimento.", "/hospital"],
    ["Avisos de chegada", "Leia o relato e a previsão de chegada. Confirme que leu, registre a chegada ou encerre o aviso. Confirmar a leitura não garante atendimento nem reserva um leito.", "/hospital/alertas"],
    ["Histórico de avisos", "Consulte os avisos anteriores e filtre pela situação para encontrar o que precisa.", "/hospital/historico"],
  ]},
  { id: "admin", title: "Para quem administra o sistema", intro: "Mantenha os cadastros e acompanhe o funcionamento do SaúdeFlow.", items: [
    ["Visão geral", "Veja o total de unidades, usuários, pedidos e avisos, além dos gráficos do sistema.", "/admin"],
    ["Unidades de saúde", "Cadastre unidades e consulte seus endereços, contatos e serviços. Você também pode ativar ou desativar uma unidade.", "/admin/unidades"],
    ["Usuários e acessos", "Veja quem tem conta, ative ou desative acessos e escolha o que cada pessoa pode fazer no sistema.", "/admin/usuarios"],
    ["Dados de outras fontes", "Atualize os cadastros vindos de fontes como CNES e DATASUS, consulte CEPs e cidades e veja quando os dados foram atualizados. Esses cadastros não mostram vagas ou leitos livres em tempo real.", "/admin/integracoes"],
    ["Histórico de alterações", "Confira quais ações foram feitas, quando aconteceram e quem as realizou.", "/admin/auditoria"],
  ]},
];

export default function HelpPage() {
  return <div className="mx-auto max-w-5xl px-4 py-10">
    <h1 className="text-3xl font-extrabold text-slate-900">Como usar o SaúdeFlow</h1>
    <p className="mt-3 max-w-3xl text-slate-600">O site ajuda a encontrar atendimento, organizar a chegada e acompanhar o pedido. Escolha abaixo a sua área para entender cada opção.</p>
    <nav aria-label="Áreas do guia" className="my-6 flex flex-wrap gap-2">{sections.map(section => <a key={section.id} href={`#${section.id}`} className="btn-secondary">{section.title}</a>)}</nav>
    <div className="mb-6 rounded-2xl bg-brand-50 p-5 text-sm text-brand-900"><strong>Está conhecendo o projeto?</strong> Use os botões de teste no topo da página para entrar como paciente, equipe da UPA, hospital ou administração. Os dados são de demonstração; os pedidos não são enviados para unidades reais.</div>
    <div className="space-y-6">{sections.map(section => <section key={section.id} id={section.id} className="scroll-mt-24">
      <Card><h2 className="text-xl font-bold text-slate-900">{section.title}</h2><p className="mt-2 text-sm text-slate-600">{section.intro}</p>
        <div className="mt-4 divide-y divide-slate-100">{section.items.map(([title, text, to]) => <details key={title} className="py-4">
          <summary className="cursor-pointer font-semibold text-brand-800">{title}</summary><p className="mt-3 text-sm leading-relaxed text-slate-600">{text}</p><Link to={to} aria-label={`Ir para: ${title}`} className="mt-3 inline-block text-sm font-semibold text-brand-700 underline">Ir para esta opção</Link>
        </details>)}</div>
      </Card>
    </section>)}</div>
    <Card className="mt-6"><h2 className="text-xl font-bold text-slate-900">Três coisas para lembrar</h2><ul className="mt-3 list-disc space-y-3 pl-5 text-sm text-slate-600">
      <li><strong>Protocolo é o número do seu pedido.</strong> Guarde para consultar o andamento e apresentar na recepção.</li>
      <li><strong>Horário de chegada é uma previsão.</strong> Pode mudar conforme o movimento e a equipe disponível. A equipe de saúde avalia quem precisa ser atendido primeiro.</li>
      <li><strong>Fila online e aviso de chegada são diferentes.</strong> A fila registra seu pedido na UPA. O aviso apenas informa ao hospital que você está a caminho.</li>
    </ul></Card>
  </div>;
}
