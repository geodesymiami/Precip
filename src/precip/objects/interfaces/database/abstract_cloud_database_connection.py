from precip.objects.interfaces.database.abstract_database_connection import AbstractDatabaseConnection


class AbstractCloudDatabaseConnection(AbstractDatabaseConnection):
    def check_db(self):
        pass


    def create_db(self):
        pass