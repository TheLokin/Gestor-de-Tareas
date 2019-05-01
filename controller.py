#!/usr/bin/python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import requests
import ast

URL = 'http://127.0.0.1:5000/worktime'

class Controller:
    def __init__(self, view):
        view.connect(self)
        self.view = view
        PageListEventsController(view.get_list_events())
        PageCalendarController(view.get_calendar())
        PageMonthlySummaryController(view.get_monthly_summary())
        NewEventController(view.get_new_event(), view)
        view.get_current_page().reload()

    def on_create_event(self, emitter, id):
        self.view.get_current_page().try_insert(id)

    def on_page_changed(self, emitter, page, page_num):
        page.reload()

class PageListEventsController:
    def __init__(self, page):
        page.connect(self)
        self.page = page

    def on_try_insert_event(self, emitter, id):
        request = requests.get(URL + '/' + str(id))
        if (request.status_code == 200):
            dictionary = ast.literal_eval(request.text)
            start_datetime = self.__parser_string(dictionary['start_date'])
            end_datetime = self.__parser_string(dictionary['end_date'])
            category = dictionary['category']
            description = dictionary['description']
            event = self.page.create(id, start_datetime, end_datetime, category, description)
            EventController(event, self.page)

    def on_remove_event(self, emitter, id):
        self.page.remove(id)

    def on_update_event(self, emitter, id):
        return

    def on_reload_list(self, emitter):
        request = requests.get(URL, params = {'startDate': '0001-01-01T00:00', 'endDate': '9999-12-31T23:59'})
        if (request.status_code == 200):
            self.page.remove_all()
            current_datetime = datetime.now()
            for dictionary in ast.literal_eval(request.text):
                end_datetime = self.__parser_string(dictionary['end_date'])
                if (end_datetime > current_datetime):
                    id = dictionary['id']
                    start_datetime = self.__parser_string(dictionary['start_date'])
                    category = dictionary['category']
                    description = dictionary['description']
                    event = self.page.create(id, start_datetime, end_datetime, category, description)
                    EventController(event, self.page)

    def __parser_string(self, string):
        return datetime.strptime(string, '%Y-%m-%dT%H:%M')

class PageCalendarController:
    def __init__(self, page):
        page.connect(self)
        self.page = page

    def on_try_insert_event(self, emitter, id):
        request = requests.get(URL + '/' + str(id))
        if (request.status_code == 200):
            date_day = self.page.get_date()
            dictionary = ast.literal_eval(request.text)
            start_datetime = self.__parser_string(dictionary['start_date'])
            end_datetime = self.__parser_string(dictionary['end_date'])
            if (self.__next_day(date_day) > start_datetime and date_day <= end_datetime):
                category = dictionary['category']
                description = dictionary['description']
                event = self.page.create(id, start_datetime, end_datetime, category, description)
                EventController(event, self.page)
            if (self.__next_month(date_day.replace(day = 1)) > start_datetime):
                self.__update()

    def on_remove_event(self, emmiter, id):
        self.page.remove(id)
        self.__update()

    def on_update_event(self, emitter, id):
        request = requests.get(URL + '/' + str(id))
        if (request.status_code == 200):
            date_day = self.page.get_date()
            date_next_day = self.__next_day(date_day)
            dictionary = ast.literal_eval(request.text)
            start_datetime = self.__parser_string(dictionary['start_date'])
            end_datetime = self.__parser_string(dictionary['end_date'])
            if (start_datetime >= date_next_day or end_datetime < date_day):
                self.page.remove(id)
            self.__update()

    def on_reload_list(self, emitter):
        request = requests.get(URL, params = {'startDate': '0001-01-01T00:00', 'endDate': '9999-12-31T23:59'})
        if (request.status_code == 200):
            self.page.remove_all()
            date_day = self.page.get_date()
            date_next_day = self.__next_day(date_day)
            current_datetime = datetime.now()
            self.page.clear_marks()
            date_month = date_day.replace(day = 1)
            date_next_month = self.__next_month(date_month)
            for dictionary in ast.literal_eval(request.text):
                start_datetime = self.__parser_string(dictionary['start_date'])
                end_datetime = self.__parser_string(dictionary['end_date'])
                if (date_next_day > start_datetime and date_day <= end_datetime):
                    id = dictionary['id']
                    category = dictionary['category']
                    description = dictionary['description']
                    event = self.page.create(id, start_datetime, end_datetime, category, description)
                    EventController(event, self.page)
                    if (current_datetime >= end_datetime):
                        event.disable_buttons()
                if (date_next_month > start_datetime):
                    if (date_month == start_datetime.replace(day = 1, hour = 0, minute = 0)):
                        date = datetime(start_datetime.year, start_datetime.month, start_datetime.day)
                    else:
                        date = datetime(date_month.year, date_month.month, 1)
                    while (date <= end_datetime and date < date_next_month):
                        self.page.mark_day(date.day)
                        date = self.__next_day(date)

    def __update(self):
        request = requests.get(URL, params = {'startDate': '0001-01-01T00:00', 'endDate': '9999-12-31T23:59'})
        if (request.status_code == 200):
            self.page.clear_marks()
            date_month = self.page.get_date().replace(day = 1)
            date_next_month = self.__next_month(date_month)
            for dictionary in ast.literal_eval(request.text):
                start_datetime = self.__parser_string(dictionary['start_date'])
                end_datetime = self.__parser_string(dictionary['end_date'])
                if (date_next_month > start_datetime):
                    if (date_month == start_datetime.replace(day = 1, hour = 0, minute = 0)):
                        date = datetime(start_datetime.year, start_datetime.month, start_datetime.day)
                    else:
                        date = datetime(date_month.year, date_month.month, 1)
                    while (date <= end_datetime and date < date_next_month):
                        self.page.mark_day(date.day)
                        date = self.__next_day(date)

    def __next_day(self, date):
        return date + timedelta(days = 1)

    def __next_month(self, date):
        try:
            return date.replace(month = date.month + 1)
        except ValueError:
            return date.replace(year = date.year + 1, month = 1)

    def __parser_string(self, string):
        return datetime.strptime(string, '%Y-%m-%dT%H:%M')

class PageMonthlySummaryController:
    def __init__(self, page):
        page.connect(self)
        self.page = page
        self.events_pending = 0

    def on_try_insert_event(self, emitter, id):
        request = requests.get(URL + '/' + str(id))
        if (request.status_code == 200):
            date_month = self.page.get_month()
            filter = self.page.get_selected_filter()
            dictionary = ast.literal_eval(request.text)
            start_datetime = self.__parser_string(dictionary['start_date'])
            category = dictionary['category']
            if (date_month <= start_datetime and start_datetime < self.__next_month(date_month) and
                (filter is None or filter == category)):
                end_datetime = self.__parser_string(dictionary['end_date'])
                description = dictionary['description']
                event = self.page.create(id, start_datetime, end_datetime, category, description)
                EventController(event, self.page)
                self.events_pending += 1
                self.page.set_events_pending(self.events_pending)

    def on_remove_event(self, emitter, id):
        self.page.remove(id)
        self.events_pending -= 1
        self.page.set_events_pending(self.events_pending)

    def on_update_event(self, emitter, id):
        request = requests.get(URL + '/' + str(id))
        if (request.status_code == 200):
            date_month = self.page.get_month()
            filter = self.page.get_selected_filter()
            dictionary = ast.literal_eval(request.text)
            start_datetime = self.__parser_string(dictionary['start_date'])
            category = dictionary['category']
            if (date_month > start_datetime or start_datetime >= self.__next_month(date_month) or
                (filter is not None and filter != category)):
                self.page.remove(id)
                self.events_pending -= 1
                self.page.set_events_pending(self.events_pending)

    def on_reload_list(self, emitter):
        self.__update()

    def on_first_month_clicked(self, emitter):
        self.page.set_month(self.__first_month(self.page.get_month()))
        self.__update()

    def on_prev_month_clicked(self, emitter):
        self.page.set_month(self.__prev_month(self.page.get_month()))
        self.__update()

    def on_next_month_clicked(self, emitter):
        self.page.set_month(self.__next_month(self.page.get_month()))
        self.__update()

    def on_last_month_clicked(self, emitter):
        self.page.set_month(self.__last_month(self.page.get_month()))
        self.__update()

    def __update(self):
        date_month = self.page.get_month()
        request = requests.get(URL, params = {'startDate': date_month.strftime('%Y-%m-%dT%H:%M'),
                                              'endDate': '9999-12-31T23:59'})
        if (request.status_code == 200):
            self.page.remove_all()
            date_next_month = self.__next_month(date_month)
            events_finished = 0
            self.events_pending = 0
            filter = self.page.get_selected_filter()
            current_datetime = datetime.now()
            for dictionary in ast.literal_eval(request.text):
                start_datetime = self.__parser_string(dictionary['start_date'])
                category = dictionary['category']
                if (start_datetime < date_next_month and (filter is None or filter == category)):
                    id = dictionary['id']
                    end_datetime = self.__parser_string(dictionary['end_date'])
                    description = dictionary['description']
                    event = self.page.create(id, start_datetime, end_datetime, category, description)
                    EventController(event, self.page)
                    if (current_datetime >= end_datetime):
                        event.disable_buttons()
                        events_finished += 1
                    else:
                        self.events_pending += 1
            self.page.set_events_finished(events_finished)
            self.page.set_events_pending(self.events_pending)

    def __first_month(self, date):
        result = date.replace(month = 1)
        if (result == date):
            return result.replace(year = date.year - 1)
        else:
            return result

    def __prev_month(self, date):
        try:
            return date.replace(month = date.month - 1)
        except ValueError:
            return date.replace(year = date.year - 1, month = 12)

    def __next_month(self, date):
        try:
            return date.replace(month = date.month + 1)
        except ValueError:
            return date.replace(year = date.year + 1, month = 1)

    def __last_month(self, date):
        result = date.replace(month = 12)
        if (result == date):
            return result.replace(year = date.year + 1)
        else:
            return result

    def __parser_string(self, string):
        return datetime.strptime(string, '%Y-%m-%dT%H:%M')

class NewEventController:
    def __init__(self, new_event, view):
        new_event.connect(self)
        self.new_event = new_event
        self.view = view
        self.__update()

    def on_datetime_changed(self, emitter):
        self.__update()

    def on_create_clicked(self, emitter):
        start_datetime = self.__parser_datetime(self.new_event.get_start_datetime())
        end_datetime = self.__parser_datetime(self.new_event.get_end_datetime())
        category = self.new_event.get_selected_category()
        description = self.new_event.get_description()
        self.new_event.reset_view()
        request = requests.post(URL, data = {'startDate': start_datetime, 'endDate': end_datetime,
                                             'category': category, 'description': description})
        if (request.status_code == 200):
            self.view.insert(ast.literal_eval(request.text)['id'])

    def __update(self):
        start_datetime = self.new_event.get_start_datetime()
        end_datetime = self.new_event.get_end_datetime()
        error_start_datetime = start_datetime is not None and datetime.now() < start_datetime
        self.new_event.set_start_datetime_state(not error_start_datetime)
        error_end_datetime = start_datetime is not None and end_datetime is not None and start_datetime < end_datetime
        self.new_event.set_end_datetime_state(not error_end_datetime)
        self.new_event.set_create_state(error_start_datetime and error_end_datetime)

    def __parser_datetime(self, datetime):
        return datetime.strftime('%Y-%m-%dT%H:%M')

class EventController:
    def __init__(self, event, page):
        event.connect(self)
        self.event = event
        self.page = page

    def on_modify_clicked(self, emitter):
        modify_event = self.event.create_modify_event()
        ModifyEventController(modify_event)
        if (modify_event.get_response()):
            id = self.event.get_id()
            start_datetime = modify_event.get_start_datetime()
            end_datetime = modify_event.get_end_datetime()
            category = modify_event.get_selected_category()
            description = modify_event.get_description()
            request = requests.put(URL + '/' + str(id), data = {'startDate': self.__parser_datetime(start_datetime),
                                                                'endDate': self.__parser_datetime(end_datetime),
                                                                'category': category, 'description': description})
            if (request.status_code == 200):
                self.event.set(start_datetime, end_datetime, category, description)
                self.page.update(id)
        modify_event.destroy()

    def on_delete_clicked(self, emitter):
        delete_event = self.event.create_delete_event()
        if (delete_event.get_response()):
            id = self.event.get_id()
            request = requests.delete(URL + '/' + str(id))
            if (request.status_code == 200):
                self.page.delete(id)
        delete_event.destroy()

    def __parser_datetime(self, datetime):
        return datetime.strftime('%Y-%m-%dT%H:%M')

class ModifyEventController:
    def __init__(self, modify_event):
        modify_event.connect(self)
        self.modify_event = modify_event
        if (datetime.now() < modify_event.get_start_datetime()):
            self.enable_start_datetime = True
        else:
            self.enable_start_datetime = False
        modify_event.enable_start_datetime(self.enable_start_datetime)

    def on_datetime_changed(self, emitter):
        start_datetime = self.modify_event.get_start_datetime()
        end_datetime = self.modify_event.get_end_datetime()
        if (self.enable_start_datetime):
            error_start_datetime = start_datetime is not None and datetime.now() < start_datetime
        else:
            error_start_datetime = True
        self.modify_event.set_start_datetime_state(not error_start_datetime)
        error_end_datetime = (start_datetime is not None and end_datetime is not None and
                              start_datetime < end_datetime and datetime.now() < end_datetime)
        self.modify_event.set_end_datetime_state(not error_end_datetime)
        self.modify_event.set_accept_state(error_start_datetime and error_end_datetime)
