from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from typing import ClassVar

from app.services.util import generate_unique_id, date_lower_than_today_error, event_not_found_error, \
    reminder_not_found_error, slot_not_available_error

@dataclass
class Reminder:

    EMAIL = "email"
    SYSTEM = "system"

    date_time: datetime
    type: str = EMAIL

    def __str__(self) -> str:
        return f"Reminder on {self.date_time} of type {self.type}"


@dataclass
class Event:

    title: str
    description: str
    date_: date
    start_at: time
    end_at: time
    reminders: list[Reminder] = field(default_factory=list)
    id: str = field(default_factory=generate_unique_id)

    def add_reminder(self, date_time: datetime, reminder_type: str = Reminder.EMAIL):
        new_reminder = Reminder(date_time, reminder_type)
        self.reminders.append(new_reminder)

    def delete_reminder(self, reminder_index: int):
        if reminder_index < len(self.reminders):
            self.reminders.pop(reminder_index)
        else:
            reminder_not_found_error()
    
    def __str__(self) -> str:
        return f"ID: {self.id}\nEvent title: {self.title}\nDescription: {self.description}\nTime: {self.start_at} - {self.end_at}"



class Day:
    def __init__(self, date_: date):
        self.date_ = date_  # Inicializa el atributo date_
        self.slots = {}  # Inicializa el atributo slots como un diccionario vacío
        self._init_slots()  # Llama al método _init_slots al final del constructor

    def _init_slots(self):
        """Inicializa el diccionario slots con las horas del día como claves (de 00:00 a 23:45, con intervalos de 15 minutos) y None como valores."""
        current_time = datetime.combine(self.date_, time(0, 0))  # Comienza a las 00:00
        end_of_day = datetime.combine(self.date_, time(23, 45))  # Termina a las 23:45
        while current_time <= end_of_day:
            self.slots[current_time.time()] = None  # Inicializa cada slot con None
            # Incrementa el tiempo en 15 minutos
            current_time += timedelta(minutes=15)

    def add_event(self, event_id: str, start_at: time, end_at: time):
        """Agrega el event_id en todos los slots que están en el rango [start_at, end_at), verificando que no haya conflictos."""
        current_time = datetime.combine(self.date_, start_at)
        end_time = datetime.combine(self.date_, end_at)
        while current_time < end_time:
            if self.slots[current_time.time()] is not None:
                slot_not_available_error()  # Lanza un error si el slot ya está ocupado
            self.slots[current_time.time()] = event_id  # Asigna el event_id al slot
            current_time += timedelta(minutes=15)

    def delete_event(self, event_id: str):
        deleted = False
        for slot, saved_id in self.slots.items():
            if saved_id == event_id:
                self.slots[slot] = None
                deleted = True
        if not deleted:
            event_not_found_error()

    def update_event(self, event_id: str, start_at: time, end_at: time):
        for slot in self.slots:
            if self.slots[slot] == event_id:
                self.slots[slot] = None

        for slot in self.slots:
            if start_at <= slot < end_at:
                if self.slots[slot]:
                    slot_not_available_error()
                else:
                    self.slots[slot] = event_id


class Calendar:
    def __init__(self):
        self.days: dict[date, Day] = {}  # Inicializa el diccionario de days vacío
        self.events: dict[str, Event] = {}  # Inicializa el diccionario de eventos vacío

    def add_event(self, title: str, description: str, date_: date, start_at: time, end_at: time) -> str:
        """Agrega un evento al calendario."""
        # Verifica si la fecha es anterior a la fecha actual
        if date_ < datetime.now().date():
            date_lower_than_today_error()

        # Si no hay un objeto Day para la fecha dada, crea uno y agrégalo al diccionario days
        if date_ not in self.days:
            self.days[date_] = Day(date_)

        # Crea un nuevo evento
        new_event = Event(title=title, description=description, date_=date_, start_at=start_at, end_at=end_at)
        
        # Agrega el evento al objeto Day correspondiente y al diccionario events
        self.days[date_].add_event(new_event.id, start_at, end_at)
        self.events[new_event.id] = new_event

        return new_event.id

    def add_reminder(self, event_id: str, date_time: datetime, type_: str = Reminder.EMAIL):
        """Agrega un recordatorio a un evento existente."""
        # Verifica si el evento con el event_id existe en el diccionario de eventos
        if event_id not in self.events:
            event_not_found_error()

        # Agrega el recordatorio al evento correspondiente
        self.events[event_id].add_reminder(date_time, type_)

    def find_available_slots(self, date_: date) -> list[time]:
        """Encuentra y retorna los espacios disponibles (slots) en una fecha dada."""
        if date_ not in self.days:
            return [time(h, m) for h in range(24) for m in [0, 15, 30, 45]]  # Si no hay eventos, todos los slots están disponibles

        # Retorna los slots disponibles, es decir, aquellos que tienen valor None
        available_slots = [slot for slot, event_id in self.days[date_].slots.items() if event_id is None]
        return available_slots
    
    def update_event(self, event_id: str, title: str, description: str, date_: date, start_at: time, end_at: time):
        event = self.events.get(event_id)
        if not event:
            event_not_found_error()

        # Verifica si la fecha ha cambiado
        is_new_date = False

        if event.date_ != date_:
            self.delete_event(event_id)
            event = Event(title=title, description=description, date_=date_, start_at=start_at, end_at=end_at)
            event.id = event_id
            self.events[event_id] = event
            is_new_date = True
            if date_ not in self.days:
                self.days[date_] = Day(date_)
            day = self.days[date_]
            day.add_event(event_id, start_at, end_at)
        else:
            event.title = title
            event.description = description
            event.date_ = date_
            event.start_at = start_at
            event.end_at = end_at

        for day in self.days.values():
            if not is_new_date and event_id in day.slots.values():
                day.delete_event(event.id)
                day.update_event(event.id, start_at, end_at)

    def delete_event(self, event_id: str):
        if event_id not in self.events:
            event_not_found_error()

        # Elimina el evento del diccionario de eventos
        self.events.pop(event_id)

        # Elimina el evento de los objetos Day
        for day in self.days.values():
            if event_id in day.slots.values():
                day.delete_event(event_id)
                break

    def find_events(self, start_at: date, end_at: date) -> dict[date, list[Event]]:
        """Encuentra eventos dentro del rango de fechas dado."""
        events: dict[date, list[Event]] = {}
        for event in self.events.values():
            if start_at <= event.date_ <= end_at:
                if event.date_ not in events:
                    events[event.date_] = []
                events[event.date_].append(event)
        return events

    def delete_reminder(self, event_id: str, reminder_index: int):
        """Elimina un recordatorio de un evento."""
        event = self.events.get(event_id)
        if not event:
            event_not_found_error()

        event.delete_reminder(reminder_index)

    def list_reminders(self, event_id: str) -> list[Reminder]:
        """Lista los recordatorios de un evento."""
        event = self.events.get(event_id)
        if not event:
            event_not_found_error()

        return event.reminders