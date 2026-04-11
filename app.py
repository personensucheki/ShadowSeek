
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
import os, re
from models import db, User
from werkzeug.security import generate_password_hash


# Klassische App entfernt/archiviert. Bitte run.py und die App-Factory-Struktur nutzen.