#!/usr/bin/python3
# -*- coding: utf-8 -*-

class Mosk:
    def __init__(self):
        self.id = 0
        self.list_events = []
        self.insert('2018-10-18T00:00', '2018-10-22T23:59', 'General', '')
        self.insert('2018-10-19T23:59', '2018-10-23T00:00', 'General', '')
        self.insert('2018-09-29T23:59', '2018-10-02T00:00', 'General', '')

    def insert(self, start_datetime, end_datetime, category, description):
        self.id += 1
        self.list_events.append({'start_datetime': start_datetime, 'end_datetime': end_datetime,
                                 'category': category, 'description': description, 'id': self.id})
        return {'id': self.id}

    def delete(self, id):
        index = 0
        for dictionary in self.list_events:
            if (dictionary['id'] == id):
                start_datetime = dictionary['start_datetime']
                end_datetime = dictionary['end_datetime']
                category = dictionary['category']
                description = dictionary['description']
                del self.list_events[index]
                return {'id': id}
            index += 1

    def update(self, id, start_datetime, end_datetime, category, description):
        for dictionary in self.list_events:
            if (dictionary['id'] == id):
                dictionary['start_datetime'] = start_datetime
                dictionary['end_datetime'] = end_datetime
                dictionary['category'] = category
                dictionary['description'] = description
                return {'id': id}
        return None

    def get(self, id):
        index = 0
        for dictionary in self.list_events:
            if (dictionary['id'] == id):
                start_datetime = dictionary['start_datetime']
                end_datetime = dictionary['end_datetime']
                category = dictionary['category']
                description = dictionary['description']
                return self.list_events[index]
            index += 1
        return None

    def get_between(self, start_datetime, end_datetime):
        result = []
        for dictionary in self.list_events:
            if (dictionary['start_datetime'] >= start_datetime and dictionary['end_datetime'] <= end_datetime):
                result.append(dictionary)
        return result
