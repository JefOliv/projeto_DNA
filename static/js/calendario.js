document.addEventListener('DOMContentLoaded', function () {
  const calendarEl = document.getElementById('calendar');
  const proxEventosEl = document.getElementById('prox-eventos');

  // Eventos iniciais de exemplo (pode carregar do servidor)
  let events = [
    { id: '1', title: 'Reunião de equipe', start: '2025-05-21' },
    { id: '2', title: 'Treinamento de segurança', start: '2025-05-25' }
  ];

  // Inicializa o calendário
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    height: 600, // altura fixa para evitar ficar gigante
    selectable: true,
    select: function (info) {
      const title = prompt('Digite o título do evento:');
      if (title) {
        const newEvent = {
          id: String(Date.now()), // id único simples
          title: title,
          start: info.startStr
        };
        events.push(newEvent);
        calendar.addEvent(newEvent);
        atualizarListaEventos();
      }
      calendar.unselect();
    },
    eventClick: function (info) {
      if (confirm(`Deseja remover o evento "${info.event.title}"?`)) {
        info.event.remove();
        events = events.filter(e => e.id !== info.event.id);
        atualizarListaEventos();
      }
    },
    events: events
  });

  calendar.render();

  // Função para atualizar a lista lateral de próximos eventos
  function atualizarListaEventos() {
    proxEventosEl.innerHTML = '';

    // Ordena eventos por data crescente
    events.sort((a, b) => new Date(a.start) - new Date(b.start));

    for (const ev of events) {
      const div = document.createElement('div');
      div.className = 'event-item';
      div.textContent = `${ev.start}: ${ev.title}`;
      div.onclick = () => {
        if (confirm(`Deseja remover o evento "${ev.title}"?`)) {
          calendar.getEventById(ev.id)?.remove();
          events = events.filter(e => e.id !== ev.id);
          atualizarListaEventos();
        }
      };
      proxEventosEl.appendChild(div);
    }
  }

  // Atualiza lista inicial
  atualizarListaEventos();
});
