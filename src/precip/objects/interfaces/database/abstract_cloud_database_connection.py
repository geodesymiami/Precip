from interfaces import AbstractDatabaseConnection


class AbstractCloudDatabaseConnection(AbstractDatabaseConnection):
    def check_db(self):
        pass


    def create_db(self):
        pass