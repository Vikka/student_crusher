class Report:
    def __init__(self, student_name):
        self.student_name = student_name
        self.score = 0
        self.notes = []

    def add_note(self, note):
        self.notes.append(note)

    def bonus(self, score):
        self.score += score

    def malus(self, score):
        self.score -= score

    def add_bonus_note(self, note: str, score: int = 1):
        self.notes.append(note)
        self.score += score

    def add_malus_note(self, note: str, score: int = 1):
        self.notes.append(note)
        self.score -= score

