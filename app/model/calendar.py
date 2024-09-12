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

                    
# TODO: Implement Calendar class here
