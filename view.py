#!/usr/bin/python3
# -*- coding: utf-8 -*-

from datetime import datetime
import gettext
import locale
import signal
import os
import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gdk, Gtk
from controller import Controller

class View:
    def __init__(self):
        self.window = Gtk.Window()
        self.window.set_title(_('Records of events'))
        self.window.set_position(Gtk.WindowPosition.CENTER)
        box = Gtk.Box()
        self.window.add(box)
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.window.set_focus(self.notebook)
        # List events
        self.list_events = PageListEventsView()
        self.notebook.append_page(self.list_events, Gtk.Label(_('List events')))
        box.pack_start(self.notebook, True, True, 0)
        # Calendar
        self.calendar = PageCalendarView()
        self.notebook.append_page(self.calendar, Gtk.Label(_('Calendar')))
        # Monthly summary
        self.monthly_summary = PageMonthlySummaryView()
        self.notebook.append_page(self.monthly_summary, Gtk.Label(_('Monthly summary')))
        # New event
        self.new_event = NewEventView()
        box.pack_start(self.new_event, True, True, 0)
        # Signals
        GObject.signal_new('try-insert', GObject.Object, GObject.SIGNAL_RUN_FIRST,
                           GObject.TYPE_NONE, (GObject.TYPE_INT,))
        GObject.signal_new('remove-event', GObject.Object, GObject.SIGNAL_RUN_FIRST,
                           GObject.TYPE_NONE, (GObject.TYPE_INT,))
        GObject.signal_new('update-event', GObject.Object, GObject.SIGNAL_RUN_FIRST,
                           GObject.TYPE_NONE, (GObject.TYPE_INT,))
        GObject.signal_new('reload-list', GObject.Object, GObject.SIGNAL_RUN_FIRST,
                           GObject.TYPE_NONE, ())
        self.window.show_all()

    def connect(self, controller):
        self.notebook.connect('try-insert', controller.on_create_event)
        self.notebook.connect('switch-page', controller.on_page_changed)
        self.window.connect('delete-event', Gtk.main_quit)

    def insert(self, id):
        self.notebook.emit('try-insert', id)

    def get_current_page(self):
        return self.notebook.get_nth_page(self.notebook.get_current_page())

    def get_list_events(self):
        return self.list_events

    def get_calendar(self):
        return self.calendar

    def get_monthly_summary(self):
        return self.monthly_summary

    def get_new_event(self):
        return self.new_event

class ListEventsView(Gtk.ScrolledWindow):
    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)
        self.set_min_content_width(760)
        self.set_propagate_natural_height(True)
        self.set_propagate_natural_width(True)
        self.set_hexpand(True)
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_border_width(18)
        self.flowbox.set_row_spacing(12)
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_sort_func(self.__sorter_datetime, None)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.set_max_children_per_line(1)
        self.add(self.flowbox)
        self.show_all()

    def create(self, id, start_datetime, end_datetime, category, description):
        event = EventView(id, start_datetime, end_datetime, category, description)
        self.flowbox.add(event)
        return event

    def remove(self, id):
        list_childrens = self.flowbox.get_children()
        position = 0
        children = list_childrens[position]
        while (children is not None and children.get_children()[0].get_id() != id):
            position += 1
            children = list_childrens[position]
        if (children is not None):
            children.destroy()

    def remove_all(self):
        for children in self.flowbox.get_children():
            children.destroy()

    def __sorter_datetime(self, event1, event2, user_data):
        start_datetime_event1 = event1.get_children()[0].get_start_datetime()
        end_datetime_event1 = event1.get_children()[0].get_end_datetime()
        start_datetime_event2 = event2.get_children()[0].get_start_datetime()
        end_datetime_event2 = event2.get_children()[0].get_end_datetime()
        if (start_datetime_event1 < start_datetime_event2):
            return -1
        else:
            if (start_datetime_event1 > start_datetime_event2):
                return 1
            else:
                if (end_datetime_event1 < end_datetime_event2):
                    return -1
                else:
                    if (end_datetime_event1 > end_datetime_event2):
                       return 1
                    else:
                        return 0

class PageView:
    def __init__(self):
        return

    def try_insert(self, id):
        raise NotImplementedError

    def delete(self, id):
        raise NotImplementedError

    def update(self, id):
        raise NotImplementedError

    def reload(self):
        raise NotImplementedError

class PageListEventsView(Gtk.Grid, PageView):
    def __init__(self):
        Gtk.Grid.__init__(self)
        PageView.__init__(self)
        # List events
        self.list_events = ListEventsView()
        self.add(self.list_events)
        self.show_all()

    def connect(self, controller):
        self.list_events.connect('try-insert', controller.on_try_insert_event)
        self.list_events.connect('remove-event', controller.on_remove_event)
        self.list_events.connect('update-event', controller.on_update_event)
        self.list_events.connect('reload-list', controller.on_reload_list)

    def try_insert(self, id):
        self.list_events.emit('try-insert', id)

    def delete(self, id):
        self.list_events.emit('remove-event', id)

    def update(self, id):
        self.list_events.emit('update-event', id)

    def reload(self):
        self.list_events.emit('reload-list')

    def create(self, id, start_datetime, end_datetime, category, description):
        return self.list_events.create(id, start_datetime, end_datetime, category, description)

    def remove(self, id):
        self.list_events.remove(id)

    def remove_all(self):
        self.list_events.remove_all()

class PageCalendarView(Gtk.Grid, PageView):
    def __init__(self):
        Gtk.Grid.__init__(self)
        PageView.__init__(self)
        # Calendar
        self.calendar = Gtk.Calendar()
        self.calendar.modify_fg(Gtk.StateType.ACTIVE, Gdk.RGBA(0.937, 0.325, 0.313, 1).to_color())
        self.calendar.drag_dest_unset()
        self.add(self.calendar)
        # List events
        self.list_events = ListEventsView()
        self.attach(self.list_events, 0, 1, 1, 1)
        self.show_all()

    def connect(self, controller):
        self.calendar.connect('day-selected', controller.on_reload_list)
        self.list_events.connect('try-insert', controller.on_try_insert_event)
        self.list_events.connect('remove-event', controller.on_remove_event)
        self.list_events.connect('update-event', controller.on_update_event)
        self.list_events.connect('reload-list', controller.on_reload_list)

    def try_insert(self, id):
        self.list_events.emit('try-insert', id)

    def delete(self, id):
        self.list_events.emit('remove-event', id)

    def update(self, id):
        self.list_events.emit('update-event', id)

    def reload(self):
        self.list_events.emit('reload-list')

    def create(self, id, start_datetime, end_datetime, category, description):
        return self.list_events.create(id, start_datetime, end_datetime, category, description)

    def remove(self, id):
        self.list_events.remove(id)

    def remove_all(self):
        self.list_events.remove_all()

    def get_date(self):
        (year, month, day) = self.calendar.get_date()
        return datetime(year, month+1, day)

    def mark_day(self, day):
        self.calendar.mark_day(day)

    def clear_marks(self):
        self.calendar.clear_marks()

class PageMonthlySummaryView(Gtk.Grid, PageView):
    def __init__(self):
        Gtk.Grid.__init__(self)
        PageView.__init__(self)
        frame = Gtk.Frame()
        grid = Gtk.Grid()
        grid.set_border_width(18)
        grid.set_column_spacing(12)
        grid.set_row_spacing(6)
        grid.set_halign(Gtk.Align.CENTER)
        frame.add(grid)
        self.attach(frame, 0, 0, 1, 1)
        box = Gtk.Box()
        box.set_margin_left(6)
        box.set_margin_right(6)
        grid.attach(box, 1, 0, 1, 2)
        self.current_month = datetime.now().replace(day = 1, hour = 0, minute = 0, second = 0, microsecond = 0)
        # Events finished
        self.events_finished_label = Gtk.Label()
        self.events_finished_label.set_halign(Gtk.Align.START)
        grid.attach(self.events_finished_label, 0, 0, 1, 1)
        # Events pending
        self.events_pending_label = Gtk.Label()
        self.events_pending_label.set_halign(Gtk.Align.START)
        grid.attach(self.events_pending_label, 0, 1, 1, 1)
        # First month
        self.first_month_button = Gtk.Button()
        self.first_month_button.set_relief(Gtk.ReliefStyle.NONE)
        self.first_month_button.set_label('<<')
        box.pack_start(self.first_month_button, True, True, 0)
        # Previous month
        self.prev_month_button = Gtk.Button()
        self.prev_month_button.set_relief(Gtk.ReliefStyle.NONE)
        self.prev_month_button.set_label('<')
        box.pack_start(self.prev_month_button, True, True, 0)
        # Month
        self.month_label = Gtk.Label()
        self.month_label.set_margin_left(12)
        self.month_label.set_margin_right(12)
        self.month_label.set_size_request(100, 10)
        self.month_label.set_justify(Gtk.Justification.CENTER)
        self.set_month(self.current_month)
        box.pack_start(self.month_label, True, True, 0)
        # Next month
        self.next_month_button = Gtk.Button()
        self.next_month_button.set_relief(Gtk.ReliefStyle.NONE)
        self.next_month_button.set_label('>')
        box.pack_start(self.next_month_button, True, True, 0)
        # Last month
        self.last_month_button = Gtk.Button()
        self.last_month_button.set_relief(Gtk.ReliefStyle.NONE)
        self.last_month_button.set_label('>>')
        box.pack_start(self.last_month_button, True, True, 0)
        # Filter
        filter_label = Gtk.Label()
        filter_label.set_label(_('Filter'))
        grid.attach(filter_label, 2, 0, 1, 2)
        self.filter_combo_box = Gtk.ComboBox()
        self.filter_combo_box.set_size_request(120, 10)
        list_filters = Gtk.ListStore(str)
        list_filters.append([_('All')])
        for new_filter in categories:
            list_filters.append([new_filter])
        self.filter_combo_box.set_model(list_filters)
        self.filter_combo_box.set_active(0)
        renderer_text = Gtk.CellRendererText()
        self.filter_combo_box.pack_start(renderer_text, True)
        self.filter_combo_box.add_attribute(renderer_text, 'text', 0)
        grid.attach(self.filter_combo_box, 3, 0, 1, 2)
        # List events
        self.list_events = ListEventsView()
        self.attach(self.list_events, 0, 1, 1, 1)
        self.show_all()

    def connect(self, controller):
        self.first_month_button.connect('clicked', controller.on_first_month_clicked)
        self.prev_month_button.connect('clicked', controller.on_prev_month_clicked)
        self.next_month_button.connect('clicked', controller.on_next_month_clicked)
        self.last_month_button.connect('clicked', controller.on_last_month_clicked)
        self.filter_combo_box.connect('changed', controller.on_reload_list)
        self.list_events.connect('try-insert', controller.on_try_insert_event)
        self.list_events.connect('remove-event', controller.on_remove_event)
        self.list_events.connect('update-event', controller.on_update_event)
        self.list_events.connect('reload-list', controller.on_reload_list)

    def try_insert(self, id):
        self.list_events.emit('try-insert', id)

    def delete(self, id):
        self.list_events.emit('remove-event', id)

    def update(self, id):
        self.list_events.emit('update-event', id)

    def reload(self):
        self.list_events.emit('reload-list')

    def create(self, id, start_datetime, end_datetime, category, description):
        return self.list_events.create(id, start_datetime, end_datetime, category, description)

    def remove(self, id):
        self.list_events.remove(id)

    def remove_all(self):
        self.list_events.remove_all()

    def get_month(self):
        return self.current_month

    def set_month(self, datetime):
        self.current_month = datetime
        self.month_label.set_label(datetime.strftime('%B').capitalize() + '\n' + datetime.strftime('%Y'))

    def set_events_finished(self, number_events):
        self.events_finished_label.set_label(_('Events finished: ') + str(number_events))

    def set_events_pending(self, number_events):
        self.events_pending_label.set_label(_('Events pending: ') + str(number_events))

    def get_selected_filter(self):
        filter = self.filter_combo_box.get_active()
        if (filter == 0):
            return None
        else:
            return str(filter-1)

class NewEventView(Gtk.Frame):
    def __init__(self):
        Gtk.Frame.__init__(self)
        self.set_label(_('  New event  '))
        self.set_label_align(0.5, 0.5)
        self.set_margin_top(12)
        self.set_margin_bottom(18)
        self.set_margin_left(18)
        self.set_margin_right(18)
        self.set_valign(Gtk.Align.START)
        grid = Gtk.Grid()
        grid.set_border_width(18)
        grid.set_column_spacing(12)
        grid.set_row_spacing(6)
        self.add(grid)
        self.datetime_format = '%H:%M %x'
        current_datetime = datetime.now().strftime(self.datetime_format)
        # Start datetime
        start_datetime_label = Gtk.Label()
        start_datetime_label.set_label(_('From'))
        start_datetime_label.set_halign(Gtk.Align.END)
        grid.add(start_datetime_label)
        self.start_datetime_entry = Gtk.Entry()
        self.start_datetime_entry.set_placeholder_text(current_datetime)
        grid.attach(self.start_datetime_entry, 1, 0, 1, 1)
        # End datetime
        self.end_datetime_label = Gtk.Label()
        self.end_datetime_label.set_label(_('To'))
        self.end_datetime_label.set_halign(Gtk.Align.END)
        grid.attach(self.end_datetime_label, 0, 1, 1, 1)
        self.end_datetime_entry = Gtk.Entry()
        self.end_datetime_entry.set_placeholder_text(current_datetime)
        grid.attach(self.end_datetime_entry, 1, 1, 1, 1)
        # Category
        category_label = Gtk.Label()
        category_label.set_label(_('Category'))
        category_label.set_halign(Gtk.Align.END)
        grid.attach(category_label, 0, 2, 1, 1)
        self.category_combo_box = Gtk.ComboBox()
        list_categories = Gtk.ListStore(str)
        for new_category in categories:
            list_categories.append([new_category])
        self.category_combo_box.set_model(list_categories)
        self.category_combo_box.set_active(0)
        renderer_text = Gtk.CellRendererText()
        self.category_combo_box.pack_start(renderer_text, True)
        self.category_combo_box.add_attribute(renderer_text, 'text', 0)
        grid.attach(self.category_combo_box, 1, 2, 1, 1)
        # Description
        description_label = Gtk.Label()
        description_label.set_label(_('Notes'))
        description_label.set_halign(Gtk.Align.END)
        grid.attach(description_label, 0, 3, 1, 1)
        description_text_view = Gtk.TextView()
        description_text_view.set_border_width(6)
        description_text_view.set_right_margin(12)
        description_text_view.set_left_margin(6)
        description_text_view.set_pixels_above_lines(6)
        description_text_view.set_pixels_below_lines(6)
        description_text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        description_text_view.set_justification(Gtk.Justification.FILL)
        self.description_text_buffer = description_text_view.get_buffer()
        description_scrolled = Gtk.ScrolledWindow()
        description_scrolled.set_size_request(200, 160)
        description_scrolled.set_hexpand(True)
        description_scrolled.add(description_text_view)
        grid.attach(description_scrolled, 1, 3, 1, 1)
        # Create
        self.create_button = Gtk.Button()
        self.create_button.set_margin_top(12)
        self.create_button.set_label(_('Create'))
        grid.attach(self.create_button, 1, 5, 1, 1)
        self.show_all()

    def connect(self, controller):
        self.start_datetime_entry.connect('changed', controller.on_datetime_changed)
        self.end_datetime_entry.connect('changed', controller.on_datetime_changed)
        self.create_button.connect('clicked', controller.on_create_clicked)

    def set_start_datetime_state(self, valid_datetime):
        self.__set_error(self.start_datetime_entry, valid_datetime)

    def set_end_datetime_state(self, valid_datetime):
        self.__set_error(self.end_datetime_entry, valid_datetime)

    def set_create_state(self, button_avaliable):
        self.create_button.set_sensitive(button_avaliable)

    def reset_view(self):
        self.start_datetime_entry.set_text('')
        self.end_datetime_entry.set_text('')
        self.category_combo_box.set_active(0)
        start_iter = self.description_text_buffer.get_start_iter()
        end_iter = self.description_text_buffer.get_end_iter()
        self.description_text_buffer.delete(start_iter, end_iter)

    def get_start_datetime(self):
        return self.__parser_string(self.start_datetime_entry.get_text().strip())

    def get_end_datetime(self):
        return self.__parser_string(self.end_datetime_entry.get_text().strip())

    def get_selected_category(self):
        return str(self.category_combo_box.get_active())

    def get_description(self):
        start_iter = self.description_text_buffer.get_start_iter()
        end_iter = self.description_text_buffer.get_end_iter()
        return self.description_text_buffer.get_text(start_iter, end_iter, True)

    def __set_error(self, entry, error):
        if error:
            entry.get_style_context().add_class('error')
        else:
            entry.get_style_context().remove_class('error')

    def __parser_string(self, string):
        try:
            return datetime.strptime(string, self.datetime_format)
        except ValueError:
            return None

class EventView(Gtk.Frame):
    def __init__(self, id, start_datetime, end_datetime, category, description):
        Gtk.Frame.__init__(self)
        self.set_valign(Gtk.Align.START)
        self.grid = Gtk.Grid()
        self.grid.set_border_width(18)
        self.grid.set_column_spacing(12)
        self.grid.set_row_spacing(6)
        box = Gtk.Box()
        box.set_margin_top(12)
        box.set_spacing(12)
        self.grid.attach(box, 1, 3, 1, 1)
        self.add(self.grid)
        # Category
        self.category_label = Gtk.Label()
        self.category_label.set_xalign(0)
        self.category_label.set_size_request(400, 10)
        self.grid.add(self.category_label)
        # Datetime
        self.datetime_label = Gtk.Label()
        self.datetime_label.set_xalign(0)
        self.datetime_label.set_size_request(400, 10)
        self.grid.attach(self.datetime_label, 0, 1, 1, 1)
        # Duration
        self.duration_label = Gtk.Label()
        self.duration_label.set_xalign(0)
        self.duration_label.set_size_request(400, 10)
        self.grid.attach(self.duration_label, 0, 2, 1, 1)
        # Description
        description_text_view = Gtk.TextView()
        description_text_view.set_editable(False)
        description_text_view.set_sensitive(False)
        description_text_view.set_border_width(6)
        description_text_view.set_right_margin(12)
        description_text_view.set_left_margin(6)
        description_text_view.set_pixels_above_lines(6)
        description_text_view.set_pixels_below_lines(6)
        description_text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        description_text_view.set_justification(Gtk.Justification.FILL)
        self.description_text_buffer = description_text_view.get_buffer()
        description_scrolled = Gtk.ScrolledWindow()
        description_scrolled.set_size_request(260, 80)
        description_scrolled.set_hexpand(True)
        description_scrolled.add(description_text_view)
        self.grid.attach(description_scrolled, 1, 0, 1, 3)
        # Modify
        self.modify_button = Gtk.Button()
        self.modify_button.set_label(_('Modify'))
        self.modify_button.set_size_request(120, 30)
        box.pack_start(self.modify_button, True, True, 0)
        # Delete
        self.delete_button = Gtk.Button()
        self.delete_button.set_label(_('Delete'))
        self.delete_button.set_size_request(120, 30)
        box.pack_start(self.delete_button, True, True, 0)
        # Initialize parameters
        self.set(start_datetime, end_datetime, category, description)
        self.id = id
        self.show_all()

    def connect(self, controller):
        self.modify_button.connect('clicked', controller.on_modify_clicked)
        self.delete_button.connect('clicked', controller.on_delete_clicked)

    def disable_buttons(self):
        self.grid.remove_row(3)

    def create_modify_event(self):
        return ModifyEventView(self.get_toplevel(), self.get_start_datetime(), self.get_end_datetime(),
                               self.get_category(), self.get_description())

    def create_delete_event(self):
        return DeleteEventView(self.get_toplevel())

    def get_start_datetime(self):
        return self.start_datetime

    def get_end_datetime(self):
        return self.end_datetime

    def get_category(self):
        return self.category

    def get_description(self):
        return self.description

    def get_id(self):
        return self.id

    def set(self, start_datetime, end_datetime, category, description):
        self.__set_category(category)
        self.__set_datetime(start_datetime, end_datetime)
        self.__set_duration(end_datetime - start_datetime)
        self.__set_description(description)
        if (self.get_parent() != None):
            self.get_parent().changed()

    def __set_category(self, category):
        self.category = category
        self.category_label.set_markup('<big><b><u>' + categories[int(category)] + '</u></b></big>')

    def __set_datetime(self, start_datetime, end_datetime):
        datetime_string = ''
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        if (start_datetime is not None and end_datetime is not None):
            if (start_datetime.date() == end_datetime.date()):
                datetime_string = start_datetime.strftime('%A, %d %b. %H:%M - ').capitalize()
                datetime_string += end_datetime.strftime('%H:%M')
            else:
                if (start_datetime.year == end_datetime.year):
                    datetime_string = start_datetime.strftime('%A, %d %b. %H:%M - ').capitalize()
                    datetime_string += end_datetime.strftime('%A, %d %b. %H:%M').capitalize()
                else:
                    if (start_datetime.year == datetime.now().year):
                        datetime_string = start_datetime.strftime('%A, %d %b. %H:%M - ').capitalize()
                        datetime_string += end_datetime.strftime('%A, %d %b. %H:%M %Y').capitalize()
                    else:
                        datetime_string = start_datetime.strftime('%A, %d %b. %H:%M %Y - ').capitalize()
                        datetime_string += end_datetime.strftime('%A, %d %b. %H:%M %Y').capitalize()
        self.datetime_label.set_label(datetime_string)

    def __set_duration(self, timedelta):
        duration_string = ''
        delta = {'days': timedelta.days}
        delta['hours'], rest = divmod(timedelta.seconds, 3600)
        delta['minutes'], delta['seconds'] = divmod(rest, 60)
        if (delta['days'] != 0):
            if (delta['days'] == 1):
                duration_string = ' {days} '.format(**delta) + _('day')
            else:
                duration_string = ' {days} '.format(**delta) + _('days')
        if (delta['hours'] != 0):
            if (delta['hours'] == 1):
                duration_string += ' {hours} '.format(**delta) + _('hour')
            else:
                duration_string += ' {hours} '.format(**delta) + _('hours')
        if (delta['minutes'] != 0):
            if (delta['minutes'] == 1):
                duration_string += ' {minutes} '.format(**delta) + _('minute')
            else:
                duration_string += ' {minutes} '.format(**delta) + _('minutes')
        self.duration_label.set_label(_('Duration: ') + duration_string)

    def __set_description(self, description):
        self.description = description
        if (description == ''):
            description = _('Notes')
        self.description_text_buffer.set_text(description)

class ModifyEventView(Gtk.Dialog):
    def __init__(self, parent, start_datetime, end_datetime, category, description):
        Gtk.Dialog.__init__(self, _('Modify'), parent, Gtk.DialogFlags.DESTROY_WITH_PARENT)
        self.set_default_response(Gtk.ResponseType.CANCEL)
        self.set_resizable(False)
        cancel_button = self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        cancel_button.set_size_request(90, 20)
        self.set_focus(cancel_button)
        accept_button = self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        accept_button.set_size_request(90, 20)
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(6)
        self.datetime_format = '%H:%M %x'
        current_datetime = datetime.now().strftime(self.datetime_format)
        # Start datetime
        start_datetime_label = Gtk.Label()
        start_datetime_label.set_label(_('From'))
        start_datetime_label.set_halign(Gtk.Align.END)
        grid.add(start_datetime_label)
        self.start_datetime_entry = Gtk.Entry()
        self.start_datetime_entry.set_placeholder_text(current_datetime)
        self.start_datetime_entry.set_text(start_datetime.strftime(self.datetime_format))
        grid.attach(self.start_datetime_entry, 1, 0, 1, 1)
        # End datetime
        self.end_datetime_label = Gtk.Label()
        self.end_datetime_label.set_label(_('To'))
        self.end_datetime_label.set_halign(Gtk.Align.END)
        grid.attach(self.end_datetime_label, 0, 1, 1, 1)
        self.end_datetime_entry = Gtk.Entry()
        self.end_datetime_entry.set_placeholder_text(current_datetime)
        self.end_datetime_entry.set_text(end_datetime.strftime(self.datetime_format))
        grid.attach(self.end_datetime_entry, 1, 1, 1, 1)
        # Category
        category_label = Gtk.Label()
        category_label.set_label(_('Category'))
        category_label.set_halign(Gtk.Align.END)
        grid.attach(category_label, 0, 2, 1, 1)
        self.category_combo_box = Gtk.ComboBox()
        list_categories = Gtk.ListStore(str)
        for new_category in categories:
            list_categories.append([new_category])
        self.category_combo_box.set_model(list_categories)
        self.category_combo_box.set_entry_text_column(0)
        self.category_combo_box.set_active(int(category))
        renderer_text = Gtk.CellRendererText()
        self.category_combo_box.pack_start(renderer_text, True)
        self.category_combo_box.add_attribute(renderer_text, 'text', 0)
        grid.attach(self.category_combo_box, 1, 2, 1, 1)
        # Description
        description_label = Gtk.Label()
        description_label.set_label(_('Notes'))
        description_label.set_halign(Gtk.Align.END)
        grid.attach(description_label, 0, 3, 1, 1)
        description_text_view = Gtk.TextView()
        description_text_view.set_border_width(6)
        description_text_view.set_right_margin(12)
        description_text_view.set_left_margin(6)
        description_text_view.set_pixels_above_lines(6)
        description_text_view.set_pixels_below_lines(6)
        description_text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        description_text_view.set_justification(Gtk.Justification.FILL)
        self.description_text_buffer = description_text_view.get_buffer()
        self.description_text_buffer.set_text(description)
        description_scrolled = Gtk.ScrolledWindow()
        description_scrolled.set_size_request(200, 160)
        description_scrolled.set_hexpand(True)
        description_scrolled.add(description_text_view)
        grid.attach(description_scrolled, 1, 3, 1, 1)
        # Content area
        box = self.get_content_area()
        box.set_border_width(18)
        box.set_spacing(18)
        box.add(grid)
        self.show_all()

    def connect(self, controller):
        self.start_datetime_entry.connect('changed', controller.on_datetime_changed)
        self.end_datetime_entry.connect('changed', controller.on_datetime_changed)

    def set_start_datetime_state(self, valid_datetime):
        self.__set_error(self.start_datetime_entry, valid_datetime)

    def set_end_datetime_state(self, valid_datetime):
        self.__set_error(self.end_datetime_entry, valid_datetime)

    def set_accept_state(self, button_avaliable):
        self.set_response_sensitive(Gtk.ResponseType.OK, button_avaliable)

    def enable_start_datetime(self, enable):
        self.start_datetime_entry.set_sensitive(enable)

    def get_start_datetime(self):
        return self.__parser_string(self.start_datetime_entry.get_text().strip())

    def get_end_datetime(self):
        return self.__parser_string(self.end_datetime_entry.get_text().strip())

    def get_selected_category(self):
        return str(self.category_combo_box.get_active())

    def get_description(self):
        start_iter = self.description_text_buffer.get_start_iter()
        end_iter = self.description_text_buffer.get_end_iter()
        return self.description_text_buffer.get_text(start_iter, end_iter, True)

    def get_response(self):
        return (Gtk.ResponseType.OK == self.run())

    def __set_error(self, entry, error):
        if error:
            entry.get_style_context().add_class('error')
        else:
            entry.get_style_context().remove_class('error')

    def __parser_string(self, string):
        try:
            return datetime.strptime(string, self.datetime_format)
        except ValueError:
            return None

class DeleteEventView(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, _('Delete'), parent, Gtk.DialogFlags.DESTROY_WITH_PARENT)
        self.set_default_response(Gtk.ResponseType.CANCEL)
        self.set_resizable(False)
        self.set_focus(self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK).get_style_context().add_class('destructive-action')
        # Delete
        delete_label = Gtk.Label()
        delete_label.set_label(_('Remove this event?'))
        # Content area
        box = self.get_content_area()
        box.set_border_width(18)
        box.set_spacing(18)
        box.add(delete_label)
        self.show_all()

    def get_response(self):
        return (Gtk.ResponseType.OK == self.run())

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    locale.setlocale(locale.LC_ALL, '')
    locale_dir = os.path.join(os.path.dirname(__file__), 'locale')
    locale.bindtextdomain('record-events', locale_dir)
    gettext.bindtextdomain('record-events', locale_dir)
    gettext.textdomain('record-events')
    _ = gettext.gettext
    categories = [_('General'), _('Study'), _('Sport')]
    Controller(View())
    Gtk.main()
