from typing import Annotated

from fastapi import Depends

fake_db = {
    1: {'id': 1, "name": "Product 1", 'category': 'category1', 'price': 42.0,
        'is_available': True, 'description': 'Test product 1'},

    2: {'id': 2, "name": "Product 2", 'category': 'category2', 'price': 123.0,
        'is_available': False, 'description': 'Tdescargsrthj'},

    3: {'id': 3, "name": "Product 3", 'category': 'category2', 'price': 333.2,
        'is_available': True, 'description': 'Test sdtyjstruyk 4'},

    4: {'id': 4, "name": "test product", 'category': 'category3',
        'price': 1233.0,
        'is_available': False, 'description': 'Test styj 5'},

    5: {'id': 5, "name": "blablabla", 'category': 'category1', 'price': 76.0,
        'is_available': True, 'description': 'Test srthaerth 1'},

}


async def get_db() -> dict:
    return fake_db


DbDep = Annotated[dict, Depends(get_db)]
