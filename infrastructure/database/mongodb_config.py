import os
from typing import Optional, Any

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:
    AsyncIOMotorClient = Any

class MongoDBConfig:
    def __init__(self):
        self.client: Optional[Any] = None
        self.database: Optional[Any] = None
        
    async def connect_to_mongo(self):
        """Conectar a MongoDB"""
        if AsyncIOMotorClient is None:
            raise ImportError("Motor is not installed. Please install it with: pip install motor")
            
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        database_name = os.getenv("DATABASE_NAME", "chat_service")
        
        self.client = AsyncIOMotorClient(mongodb_url)
        self.database = self.client[database_name]
        
        # Verificar conexión
        try:
            if self.client:
                await self.client.admin.command('ping')
                print("✅ Conexión exitosa a MongoDB")
        except Exception as e:
            print(f"❌ Error conectando a MongoDB: {e}")
            raise
    
    async def close_mongo_connection(self):
        """Cerrar conexión a MongoDB"""
        if self.client:
            self.client.close()
            print("🔴 Conexión a MongoDB cerrada")
    
    def get_database(self):
        """Obtener instancia de la base de datos"""
        return self.database

# Instancia global de configuración
mongo_config = MongoDBConfig()

async def get_database():
    """Función helper para obtener la base de datos"""
    return mongo_config.get_database() 