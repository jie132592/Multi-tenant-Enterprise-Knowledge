"""部门服务"""
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session

from app.models import Department, User, KnowledgeBase


class DepartmentService:
    """部门服务"""

    def __init__(self, db: Session):
        self.db = db

    def create(
            self,
            tenant_id: int,
            name: str,
            code: str,
            parent_id: int = None,
            description: str = "",
    ):
        department = Department(
            tenant_id=tenant_id,
            name=name,
            code=code,
            parent_id=parent_id,
            description=description,
        )
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        return department

    def get(self, tenant_id: int, dep_id: int) -> Optional[Department]:
        return self.db.query(Department).filter(
            Department.id == dep_id,
            Department.tenant_id == tenant_id
        ).first()

    def list(
        self,
        tenant_id: int,
        page: int = 1,
        page_size: int = 100,
        keyword: str = None
    ) -> Tuple[List[Department], int]:
        """获取部门列表"""
        query = self.db.query(Department).filter(
            Department.tenant_id == tenant_id
        )

        if keyword:
            query = query.filter(Department.name.like(f"%{keyword}%"))

        total = query.count()
        depts = query.order_by(Department.created_at.desc())\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()
        return depts, total

    def list_all(self, tenant_id: int) -> List[Department]:
        """获取所有部门"""
        return self.db.query(Department).filter(
            Department.tenant_id == tenant_id
        ).order_by(Department.created_at).all()

    def update(
        self,
        dept_id: int,
        tenant_id: int,
        name: str = None,
        code: str = None,
        parent_id: int = None,
        leader_user_id: int = None,
        description: str = None
    ) -> Optional[Department]:
        """更新部门"""
        dept = self.get(dept_id, tenant_id)
        if not dept:
            return None

        if name is not None:
            dept.name = name
        if code is not None:
            dept.code = code
        if parent_id is not None:
            dept.parent_id = parent_id
        if leader_user_id is not None:
            dept.leader_user_id = leader_user_id
        if description is not None:
            dept.description = description

        self.db.commit()
        self.db.refresh(dept)
        return dept

    def delete(self, tenant_id: int, dep_id: int) -> bool:
        """
        删除部门
        注意: 不会级联删除子部门，需要先删除子部门
        删除后会:
        - 将该部门下用户的 department_id 设为 NULL
        - 将该部门负责人的 leader_user_id 设为 NULL
        """
        dep = self.get(tenant_id, dep_id)
        if not dep:
            return False

        # 判断有没有子部门
        children = self.db.query(Department).filter(
            Department.parent_id == dep_id,
            Department.tenant_id == tenant_id
        ).count()
        if children > 0:
            raise ValueError("请先删除子部门")
        # 该部门下用户的department_id设置为None
        self.db.query(User).filter(
            User.department_id == dep_id,
        ).update({"department_id": None})

        # 引用该部门的知识库department_id设置为None
        self.db.query(KnowledgeBase).filter(
            KnowledgeBase.department_id == dep_id,
        ).update({"department_id": None})

        self.db.delete(dep)
        self.db.commit()
        return True

    def get_user_count(self, dep_id: int) -> int:
        """获取部门用户数量"""
        return self.db.query(User).filter(User.department_id == dep_id).count()

    def get_leader_username(self, leader_user_id: int) -> str:
        if not leader_user_id:
            return ""
        user = self.db.query(User).filter(User.id == leader_user_id).first()
        return user.username if user else ''

    def build_tree(self, tenant_id: int) -> List[dict]:
        """构建部门树"""
        deps = self.list_all(tenant_id)

        # 转换为 dict
        deps_dict = {}
        for dep in deps:
            deps_dict[dep.id] = {
                "id": dep.id,
                "name": dep.name,
                "code": dep.code,
                "parent_id": dep.parent_id,
                "description": dep.description or "",
                "user_count": self.get_user_count(dep.id),
                "children": []
            }

        # 构建树
        roots = []
        for dep in deps:
            if dep.parent_id and dep.parent_id in deps_dict:
                deps_dict[dep.parent_id]["children"].append(deps_dict[dep.id])
            else:
                roots.append(deps_dict[dep.id])

        return roots