# -*- coding: utf-8 -*-

import json

from typing import Optional

from db import collection_domain

class DomainObject:
    def __init__(self, name, label, instructions, googleSelectedDetails, columns=[]):
        self.name = name
        self.label = label
        self.instructions = instructions
        self.googleSelectedDetails = googleSelectedDetails
        self.columns = columns

    def __str__(self):
        return f"{self.label}"

    def __repr__(self):
        return f"{self.label}"
    
    def to_dict(self):
        return {
            "name": self.name,
            "label": self.label,
            "instructions": self.instructions,
            "googleSelectedDetails": self.googleSelectedDetails,
            "columns": self.columns
        }
    
    @staticmethod
    def from_dict(data: dict):
        return DomainObject(
            name=data["name"],
            label=data["label"],
            instructions=data["instructions"],
            googleSelectedDetails=data["googleSelectedDetails"],
            columns=data.get("columns", [])
        )
    
    @staticmethod
    def from_json(json_data: str):
        return DomainObject.from_dict(json.loads(json_data))
    
    def to_json(self):
        return json.dumps(self.to_dict())
    
    def save(self):
        collection_domain.insert_one(self.to_dict())

    @staticmethod

    def load(name: str) -> Optional['DomainObject']:
        """
        Load domain by name
        """
        data = collection_domain.find_one({"name": name})
        if data:
            return DomainObject.from_dict(data)
        return None
    
    @staticmethod
    def load_all():
        return [DomainObject.from_dict(data) for data in collection_domain.find()]
    
    @staticmethod
    def delete(name: str):
        collection_domain.delete_one({"name": name})

    @staticmethod
    def delete_all():
        collection_domain.delete_many({})

    def update(self):
        try:
            collection_domain.update_one({"name": self.name}, {"$set": self.to_dict()})
        except Exception as e:
            print('Error updating domain: ', e)
            return False
    @staticmethod
    def find_by_condition(condition: dict):
        """Find domain by condition"""
        return [DomainObject.from_dict(data) for data in collection_domain.find(condition)]
