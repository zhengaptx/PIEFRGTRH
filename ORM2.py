import os
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from datetime import date
import ttkbootstrap as ttk
from PIL import ImageTk, Image
import ast

# 创建数据库引擎，这里使用SQLite示例，你可按需更换数据库类型（如MySQL等）
engine = create_engine('sqlite:///school_data.db')
# 创建基类
Base = declarative_base()

# 定义数据模型类（对应数据库中的表结构）
class Student(Base):
    __tablename__ ='students'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    birth_date = Column(Date)  # 存储标准日期格式的出生日期
    age = Column(Integer)
    exam_scores = relationship("StudentExamScore", back_populates="student")  # 建立与成绩关联表的关系
    exam_questions = relationship("StudentQuestion", back_populates="student")  # 建立与学生题目关联表的关系

    def calculate_age(self):
        """
        根据出生日期计算当前年龄
        """
        current_year = date.today().year
        birth_year = self.birth_date.year
        return current_year - birth_year

# 定义学生考试成绩关联表
class StudentExamScore(Base):
    __tablename__ ='student_exam_scores'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    exam_id = Column(Integer, ForeignKey('exams.id'))
    score = Column(Integer)
    student = relationship("Student", back_populates="exam_scores")
    exam = relationship("Exam", back_populates="student_scores")

# 定义学生题目关联表
class StudentQuestion(Base):
    __tablename__ ='student_questions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    student = relationship("Student", back_populates="exam_questions")
    question = relationship("Question", back_populates="students")

# 考试数据模型类
class Exam(Base):
    __tablename__ = 'exams'
    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_number = Column(String)
    organization = Column(String)
    time = Column(String)
    questions = relationship("Question", secondary="exam_question_association", back_populates="exams")
    students = relationship("Student", secondary="student_exam_association", back_populates="exams")
    paper_file = Column(String)
    student_scores = relationship("StudentExamScore", back_populates="exam")

# 定义题目数据模型类
class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_number = Column(String)
    section = Column(String)
    difficulty = Column(String)
    image_path = Column(String)  # 新增用于存储题目图片路径的字段
    exams = relationship("Exam", secondary="exam_question_association", back_populates="questions")
    students = relationship("Student", secondary="student_question_association", back_populates="questions")
    content = Column(Text)
    file = Column(String)
    related_questions = Column(Text)

# 标签数据模型类
class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String)
    questions = relationship("Question", secondary="tag_question_association", back_populates="tags")
    exams = relationship("Exam", secondary="tag_exam_association", back_populates="tags")

# 数据库管理类，整合各个类的操作，并处理数据的同步更新等功能
class DatabaseManager:
    def __init__(self):
        # 创建会话工厂，绑定数据库引擎
        self.Session = sessionmaker(bind=engine)
        # 创建所有表（如果不存在）
        Base.metadata.create_all(engine)

    def add_student(self, student_info):
        """
        新增学生信息到数据库
        :param student_info: 包含学生信息的字典，例如{"name": "张三", "birth_date": date(2000, 1, 1), "exam_scores": [], "exam_questions": []}
        """
        try:
            session = self.Session()
            new_student = Student(**student_info)
            new_student.age = new_student.calculate_age()  # 新增学生时计算并设置年龄
            session.add(new_student)
            session.commit()
            session.close()
            return True, "学生信息添加成功！"
        except ValueError as ve:
            return False, f"输入的数据格式有误，请检查，具体错误: {str(ve)}"
        except Exception as e:
            return False, f"添加学生信息出现未知错误，请查看相关日志或终端输出，错误信息: {str(e)}"

    def delete_student(self, student_name):
        """
        根据学生姓名从数据库删除学生信息
        """
        try:
            session = self.Session()
            student = session.query(Student).filter(Student.name == student_name).first()
            if student:
                # 先删除与该学生相关的成绩关联记录和题目关联记录
                for score in student.exam_scores:
                    session.delete(score)
                for question in student.exam_questions:
                    session.delete(question)
                session.delete(student)
                session.commit()
                session.close()
                return True, "学生信息删除成功！"
            else:
                return False, f"未找到姓名为 {student_name} 的学生，请检查输入是否正确"
        except Exception as e:
            return False, f"删除学生信息出现未知错误，请查看相关日志或终端输出，错误信息: {str(e)}"

    def update_student(self, student_info):
        """
        更新学生信息到数据库
        """
        try:
            session = self.Session()
            student_id = student_info.get('id')
            if student_id:
                student = session.query(Student).filter(Student.id == student_id).first()
                if student:
                    for key, value in student_info.items():
                        setattr(student, key, value)
                    student.age = student.calculate_age()  # 更新学生信息时重新计算年龄
                    session.commit()
                    session.close()
                    return True, "学生信息修改成功！"
                else:
                    return False, "未找到对应ID的学生信息，请检查输入是否正确"
            else:
                return False, "未提供有效的学生ID，无法进行修改操作，请检查输入"
        except ValueError as ve:
            return False, f"输入的数据格式有误，请检查，具体错误: {str(ve)}"
        except Exception as e:
            return False, "更新学生信息出现未知错误，请查看相关日志或终端输出，错误信息: {str(e)}"

    def get_student_data(self):
        """
        从数据库获取所有学生数据
        """
        try:
            session = self.Session()
            students = session.query(Student).all()
            session.close()
            return students
        except Exception as e:
            return []

    def add_exam(self, exam_info):
        """
        新增考试信息到数据库，同时处理与学生、题目等的关联关系
        """
        try:
            session = self.Session()
            new_exam = Exam(**exam_info)
            session.add(new_exam)

            # 处理考试与学生的关联关系（假设exam_info中包含参与考试的学生ID列表'student_ids'）
            student_ids = exam_info.get('student_ids', [])
            if not isinstance(student_ids, list) or not all(isinstance(s_id, int) for s_id in student_ids):
                return False, "学生ID列表格式不正确，请检查输入数据"
            for student_id in student_ids:
                student = session.query(Student).filter(Student.id == student_id).first()
                if student:
                    student_exam_score = StudentExamScore(student=student, exam=new_exam, score=None)
                    session.add(student_exam_score)

            # 处理考试与题目的关联关系（假设exam_info中包含题目ID列表'question_ids'）
            question_ids = exam_info.get('question_ids', [])
            if not isinstance(question_ids, list) or not all(isinstance(q_id, int) for q_id in question_ids):
                return False, "题目ID列表格式不正确，请检查输入数据"
            for question_id in question_ids:
                question = session.query(Question).filter(Question.id == question_id).first()
                if question:
                    new_exam.questions.append(question)

            session.commit()
            session.close()
            return True, "考试信息添加成功！"
        except Exception as e:
            return False, f"添加考试信息出现未知错误，请查看相关日志或终端输出，错误信息: {str(e)}"

    def update_exam(self, exam_info):
        """
        更新考试信息到数据库
        """
        try:
            session = self.Session()
            exam_id = exam_info.get('id')
            if exam_id:
                exam = session.query(Exam).filter(Exam.id == exam_id).first()
                if exam:
                    for key, value in exam_info.items():
                        setattr(exam, key, value)
                    session.commit()
                    session.close()
                    return True, "考试信息修改成功！"
                else:
                    return False, "未找到对应ID的考试信息，请检查输入是否正确"
            else:
                return False, "未提供有效的考试ID，无法进行修改操作，请检查输入"
        except ValueError as ve:
            return False, f"输入的数据格式有误，请检查，具体错误: {str(ve)}"
        except Exception as e:
            return False, "更新考试信息出现未知错误，请查看相关日志或终端输出，错误信息: {str(e)}"

    def delete_exam(self, exam_number):
        """
        根据考试编号从数据库删除考试信息
        """
        try:
            session = self.Session()
            exam = session.query(Exam).filter(Exam.exam_number == exam_number).first()
            if exam:
                # 先删除与该考试相关的学生成绩关联记录和题目关联记录
                for score in exam.student_scores:
                    session.delete(score)
                for question in exam.questions:
                    session.delete(question)
                session.delete(exam)
                session.commit()
                session.close()
                return True, "考试信息删除成功！"
            else:
                return False, "未找到编号为 {exam_number} 的考试，请检查输入是否正确"
        except Exception as e:
            return False, f"删除考试信息出现未知错误，请查看相关日志或终端输出，错误信息: {str(e)}"

    def add_question(self, question_info):
        """
        新增题目信息到数据库
        """
        try:
            session = self.Session()
            new_question = Question(**question_info)
            session.add(new_question)
            session.commit()
            session.close()
            return True, "题目信息添加成功！"
        except ValueError as ve:
            return False, f"输入的数据格式有误，请检查，具体错误: {str(ve)}"
        except Exception as e:
            return False, f"添加题目信息出现未知错误，请查看相关日志或终端输出，错误信息: {str(e)}"

    def update_question(self, question_info):
        """
        更新题目信息到数据库
        """
        try:
            session = self.Session()
            question_id = question_info.get('id')
            if question_id:
                question = session.query(Question).filter(Question.id == question_id).first()
                if question:
                    for key, value in question_info.items():
                        setattr(question, key, value)
                    session.commit()
                    session.close()
                    return True, "题目信息修改成功！"
                else:
                    return False, "未找到对应ID的题目信息，请检查输入是否正确"
            else:
                return False, "未提供有效的题目ID，无法进行修改操作，请检查输入"
        except ValueError as ve:
            return False, f"输入的数据格式有误，请检查，具体错误: {str(ve)}"
        except Exception as e:
            return False, "更新题目信息出现未知错误，请查看相关日志或终端输出，错误信息: {str(e)}"

    def delete_question(self, question_number):
        """
        根据题目编号从数据库删除题目信息
        """
        try:
            session = self.Session()
            question = session.query(Question).filter(Question.question_number == question_number).first()
            if question:
                session.delete(question)
                session.commit()
                session.close()
                return True, "题目信息删除成功！"
            else:
                return False, "未找到编号为 {question_number} 的题目，请检查输入是否正确"
        except Exception as e:
            return False, "删除题目信息出现未知错误，请查看相关日志或终端输出，错误信息: {str(e)}"

    def add_tag(self, tag_info):
        """
        新增标签信息到数据库
        """
        try:
            session = self.Session()
            new_tag = Tag(**tag_info)
            session.add(new_tag)
            session.commit()
            session.close()
            return True, "标签信息添加成功！"
        except ValueError as ve:
            return False, f"输入的数据格式有误，请检查，具体错误: {str(ve)}"
        except Exception as e:
            return False, "添加标签信息出现未知错误，请查看相关日志或终端输出，错误信息: {str(e)}"

    def update_tag(self, tag_info):
        """
        更新标签信息到数据库
        """
        try:
            session = self.Session()
            tag_id = tag_info.get('id')
            if tag_id:
                tag = session.query(Tag).filter(Tag.id == tag_id).first()
                if tag:
                    for key, value in tag_info.items():
                        setattr(tag, key, value)
                    session.commit()
                    session.close()
                    return True, "标签信息修改成功！"
                else:
                    return False, "未找到对应ID的标签信息，请检查输入是否正确"
            else:
                return False, "未提供有效的标签ID，无法进行修改操作，请检查输入"
        except ValueError as ve:
            return False, "输入的数据格式有误，请检查，具体错误: {str(ve)}"
        except Exception as e:
            return False, "更新标签信息出现未知错误，请查看相关日志或终端输出，错误信息: {str(e)}"

    def delete_tag(self, tag_content):
        """
        根据标签内容从数据库删除标签信息
        """
        try:
            session = self.Session()
            tag = session.query(Tag).filter(Tag.content == tag_content).first()
            if tag:
                session.delete(tag)
                session.commit()
                session.close()
                return True, "标签信息删除成功！"
            else:
                return False, "未找到内容为 {tag_content} 的标签，请检查输入是否正确"
        except Exception as e:
            return False, "删除标签信息出现未知错误，请查看相关日志或终端输出，错误信息: {str(e)}"

    def backup_data(self):
        """
        建立备份数据文件，将所有数据保存在备份文件夹中，设置为只读
        """
        backup_folder = "backup"
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)

        # 备份学生数据
        try:
            session = self.Session()
            students = session.query(Student).all()
            student_data = []
            for s in students:
                scores = [{"exam_id": score.exam.id, "score": score.score} for score in s.exam_scores]
                questions = [q.id for q in s.exam_questions]
                student_data.append({
                    "name": s.name,
                    "birth_date": s.birth_date.strftime('%Y-%m-%d'),
                    "age": s.age,
                    "exam_scores": scores,
                    "exam_questions": questions
                })
            with open(os.path.join(backup_folder, "students.csv"), "w", newline='') as csvfile:
                fieldnames = ["name", "birth_date", "age", "exam_scores", "exam_questions"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for student in student_data:
                    writer.writerow(student)
            os.chmod(os.path.join(backup_folder, "students.csv"), 0o444)
            session.close()
        except Exception as e:
            print(f"备份学生数据出现错误: {str(e)}")

        # 备份考试数据等其他备份逻辑，此处省略部分重复代码展示

    def get_exam_data(self):
        """
        从数据库获取所有考试数据
        """
        try:
            session = self.Session()
            exams = session.query(Exam).all()
            session.close()
            return exams
        except Exception as e:
            return []

    def get_question_data(self):
        """
        从数据库获取所有题目数据
        """
        try:
            session = self.Session()
            questions = session.query(Question).all()
            session.close()
            return questions
        except Exception as e:
            return []

    def get_tag_data(self):
        """
        从数据库获取所有标签数据
        """
        try:
            session = self.Session()
            tags = session.query(Tag).all()
            session.close()
            return tags
        except Exception as e:
            return []

# 图形界面交互类，用于创建命令行和图形界面交互
class GUI:
    def __init__(self, database_manager):
        self.database_manager = database_manager
        self.root = tk.Tk()
        self.root.title("数据库管理系统")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        self.current_user = None
        self.login_status_var = tk.IntVar()
        self.login_frame = None
        self.style_config()

    def style_config(self):
        """
        配置界面组件的公共样式，如字体、颜色等，保持风格统一
        """
        self.font_family = "Arial"
        self.font_size = 12
        self.button_bg_color = "#4CAF50"
        self.button_fg_color = "white"
        self.label_bg_color = "#F0F0F0"

    def show_login_interface(self):
        """
        在主界面上显示登录界面
        """
        if self.login_frame:
            self.login_frame.destroy()

        # 创建新的登录界面框架，应用样式配置
        self.login_frame = tk.Frame(self.root, bg=self.label_bg_color)
        self.login_frame.pack(pady=100)

        tk.Label(self.login_frame, text="请选择登录身份：", font=(self.font_family, self.font_size), bg=self.label_bg_color).pack()
        tk.Button(self.login_frame, text="管理员", command=self.admin_login, font=(self.font_family, self.font_size),
                  bg=self.button_bg_color, fg=self.button_fg_color).pack(pady=10)
        tk.Button(self.login_frame, text="游客", command=self.guest_login, font=(self.font_family, self.font_size),
                  bg=self.button_bg_color, fg=self.button_fg_color).pack()

    def admin_login(self):
        """
        管理员登录逻辑，验证密码
        """
        self.login_frame.destroy()
        self.login_frame = None

        # 在主界面上创建用户名和密码输入框，应用样式配置
        username_label = tk.Label(self.root, text="用户名:", font=(self.font_family, self.font_size), bg=self.label_bg_color)
        username_label.pack(pady=10)
        username_entry = tk.Entry(self.root, font=(self.font_family, self.font_size))
        username_entry.pack(pady=5)
        password_label = tk.Label(self.root, text="密码:", font=(self.font_family, self.font_size), bg=self.label_bg_color)
        password_label.pack(pady=10)
        password_entry = tk.Entry(self.root, show="*", font=(self.font_family, self.font_size))
        password_entry.pack(pady=5)

        verify_button = tk.Button(self.root, text="登录", font=(self.font_family, self.font_size),
                                  bg=self.button_bg_color, fg=self.button_fg_color)
        def delay_verify():
            input_username = username_entry.get()
            input_password = password_entry.get()
            self.verify_password(input_username, input_password, 'admin')
        verify_button["command"] = lambda: self.root.after(100, delay_verify)
        verify_button.pack(pady=10)

    def guest_login(self):
        """
        游客登录逻辑，直接登录
        """
        try:
            self.current_user = 'guest'
            if not hasattr(self, '_guest_interface_shown'):
                self.login_frame.destroy()
                self.login_frame = None
                self.root.update_idletasks()
                self.root.update()
                self.login_status_var.set(1)  # 设置登录状态变量，表示登录成功
                self.show_guest_interface()
                self._guest_interface_shown = True
            else:
                return
        except:
            messagebox.showerror("错误", "游客登录界面显示出现问题，请重试")

    def verify_password(self, input_username, input_password, user_type):
        """
        验证密码是否正确
        :param input_username: 输入的用户名
        :param input_password: 输入的密码
        :param user_type: 用户类型，如 'admin'
        """
        if input_username == "" or input_password == "":
            messagebox.showwarning("警告", "请输入用户名和密码")
            return
        if user_type == 'admin' and input_username == 'admin' and input_password == "123456":
            try:
                self.current_user = 'admin'
                if not hasattr(self, '_admin_interface_shown'):
                    for widget in self.root.winfo_children():
                        if widget.winfo_class() not in ['Frame', 'Menu']:
                            widget.destroy()
                    self.root.update_idletasks()
                    self.root.update()
                    self.login_status_var.set(1)  # 设置登录状态变量，表示登录成功
                    self.show_admin_interface()
                    self._admin_interface_shown = True
                else:
                    return
            except Exception as e:
                messagebox.showerror("错误", f"管理员界面显示出现问题，请重试，具体错误: {str(e)}")
        else:
            messagebox.showerror("错误", "用户名或密码错误，请重新输入")
            self.show_login_interface()

    def run(self):
        """
        运行图形界面，显示主界面并根据用户权限提供相应操作入口
        """
        login_attempted = False
        while True:
            if not login_attempted:
                self.show_login_interface()

            if self.login_status_var.get():
                if self.current_user == 'admin':
                    try:
                        print("成功登入管理员界面")
                        break
                    except Exception as e:
                        messagebox.showerror("错误", f"管理员界面显示出现问题，请重试，具体错误: {str(e)}")
                        self.current_user = None
                        continue
                elif self.current_user == 'guest':
                    try:
                        print("成功登入游客界面")
                        break
                    except Exception as e:
                        messagebox.showerror("错误", f"游客界面显示出现问题，请重试，具体错误: {str(e)}")
                        self.current_user = None
                        continue
                else:
                    messagebox.showerror("错误", "登录出现未知错误，请重新登录")
                    self.current_user = None
                    continue
            else:
                self.root.update_idletasks()
                self.root.update()

            login_attempted = True

        self.root.mainloop()

    def show_admin_interface(self):
        """
        展示管理员界面，包含各种可操作功能按钮等，添加了菜单栏进行功能分类展示
        """
        admin_frame = tk.Frame(self.root, bg=self.label_bg_color)
        admin_frame.pack(pady=20, padx=20)

        # 创建菜单栏
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # 学生管理菜单
        student_menu = tk.Menu(menu_bar, tearoff=0)
        student_menu.add_command(label="新增学生（表单方式）", command=self.add_student_form)
        student_menu.add_command(label="新增学生（文件导入）", command=self.add_student_file)
        student_menu.add_command(label="修改学生（表单方式）", command=self.update_student_form)
        student_menu.add_command(label="修改学生（文件导入）", command=self.update_student_file)
        student_menu.add_command(label="删除学生", command=self.delete_student)
        student_menu.add_command(label="查看学生数据", command=self.view_student_data)
        menu_bar.add_cascade(label="学生管理", menu=student_menu)

        # 考试管理菜单
        exam_menu = tk.Menu(menu_bar, tearoff=0)
        exam_menu.add_command(label="新增考试", command=self.add_exam_file)
        exam_menu.add_command(label="修改考试", command=self.update_exam_file)
        exam_menu.add_command(label="删除考试", command=self.delete_exam)
        exam_menu.add_command(label="查看考试数据", command=self.view_exam_data)
        menu_bar.add_cascade(label="考试管理", menu=exam_menu)

        # 题目管理菜单
        question_menu = tk.Menu(menu_bar, tearoff=0)
        question_menu.add_command(label="新增题目", command=self.add_question_file)
        question_menu.add_command(label="修改题目", command=self.update_question_file)
        question_menu.add_command(label="新增题目", command=self.delete_question)
        question_menu.add_command(label="查看题目数据", command=self.view_question_data)
        menu_bar.add_cascade(label="题目管理", menu=question_menu)

        # 标签管理菜单
        tag_menu = tk.Menu(menu_bar, tearoff=0)
        tag_menu.add_command(label="新增标签", command=self.add_tag_file)
        tag_menu.add_command(label="修改标签", command=self.update_tag_file)
        tag_menu.add_command(label="删除标签", command=self.delete_tag)
        tag_menu.add_command(label="查看标签数据", command=self.view_tag_data)
        menu_bar.add_cascade(label="标签管理", menu=tag_menu)

        # 分析相关菜单
        analysis_menu = tk.Menu(menu_bar, tearoff=0)
        analysis_menu.add_command(label="分析学生（按考试）", command=self.analyze_student_by_exam)
        analysis_menu.add_command(label="分析学生（按标签）", command=self.analyze_student_by_tag)
        analysis_menu.add_command(label="分析学生（按题目）", command=self.analyze_student_by_question)
        menu_bar.add_cascade(label="分析功能", menu=analysis_menu)

        tk.Label(admin_frame, text="管理员界面，可进行数据管理操作", font=(self.font_family, self.font_size + 2), bg=self.label_bg_color).pack(pady=10)

    def show_guest_interface(self):
        """
        展示游客界面，只提供查看数据功能按钮等，添加了菜单栏进行功能分类展示
        """
        guest_frame = tk.Frame(self.root, bg=self.label_bg_color)
        guest_frame.pack(pady=20, padx=20)

        # 创建菜单栏
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # 学生管理菜单（游客仅可查看学生数据）
        student_menu = tk.Menu(menu_bar, tearoff=0)
        student_menu.add_command(label="查看学生数据", command=self.view_student_data)
        menu_bar.add_cascade(label="学生管理", menu=student_menu)

        # 考试管理菜单（游客仅可查看考试数据）
        exam_menu = tk.Menu(menu_bar, tearoff=0)
        exam_menu.add_command(label="查看考试数据", command=self.view_exam_data)
        menu_bar.add_cascade(label="考试管理", menu=exam_menu)

        # 题目管理菜单（游客仅可查看题目数据）
        question_menu = tk.Menu(menu_bar, tearoff=0)
        question_menu.add_command(label="查看题目数据", command=self.view_question_data)
        menu_bar.add_cascade(label="题目管理", menu=question_menu)

        # 标签管理菜单（游客仅可查看标签数据）
        tag_menu = tk.Menu(menu_bar, tearoff=0)
        tag_menu.add_command(label="查看标签数据", command=self.view_tag_data)
        menu_bar.add_cascade(label="标签管理", menu=tag_menu)

        # 分析相关菜单（游客可查看部分分析功能结果）
        analysis_menu = tk.Menu(menu_bar, tearoff=0)
        analysis_menu.add_command(label="分析学生（按考试）", command=self.analyze_student_by_exam)
        analysis_menu.add_command(label="分析学生（按标签）", command=self.analyze_student_by_tag)
        analysis_menu.add_command(label="分析学生（按题目）", command=self.analyze_student_by_question)
        menu_bar.add_cascade(label="分析功能", menu=analysis_menu)

        tk.Label(guest_frame, text="游客界面，仅可查看数据", font=(self.font_family, self.font_size + 2), bg=self.label_bg_color).pack(pady=10)

    def add_student_form(self):
        """
        通过表单方式新增学生信息，使用填空和下拉列表等界面组件，添加了输入提示和默认值设置等优化
        """
        add_student_frame = tk.Frame(self.root, bg=self.label_bg_color)
        add_student_frame.pack(pady=20, padx=20)

        # 姓名输入框
        name_label = tk.Label(add_student_frame, text="姓名：", font=(self.font_family, self.font_size), bg=self.label_bg_color)
        name_label.grid(row=0, column=0, pady=5, padx=5)
        name_entry = tk.Entry(add_student_frame, font=(self.font_family, self.font_size))
        name_entry.grid(row=0, column=1, pady=5, padx=5)
        name_tooltip = ttk.Tooltip(name_label, "请输入学生的姓名，长度在1-20个字符之间", bootstyle="light")

        # 出生日期输入框，使用日期选择组件（这里假设使用tkcalendar等第三方库实现，需额外安装）
        birth_date_label = tk.Label(add_student_frame, text="出生日期：", font=(self.font_family, self.font_size), bg=self.label_bg_color)
        birth_date_label.grid(row=1, column=0, pady=5, padx=5)
        from tkcalendar import DateEntry
        birth_date_entry = DateEntry(add_student_frame, font=(self.font_family, self.font_size), width=12, background='darkblue',
                                     foreground='white', borderwidth=2)
        birth_date_entry.grid(row=1, column=1, pady=5, padx=5)
        birth_date_tooltip = ttk.Tooltip(birth_date_label, "请选择合法的日期格式（YYYY-MM-DD）", bootstyle="light")
        def validate_birth_date(event):
            try:
                birth_date_entry.get_date()  # 尝试获取日期，若格式不对会抛出异常
            except ValueError:
                messagebox.showerror("错误", "请输入正确的日期格式（YYYY-MM-DD）")
        birth_date_entry.bind("<FocusOut>", validate_birth_date)

        # 考试成绩字段，默认设置为空列表
        exam_scores_var = tk.StringVar(value="[]")
        tk.Label(add_student_frame, text="考试成绩（初始为空列表，可后续修改）：", font=(self.font_family, self.font_size), bg=self.label_bg_color).grid(row=2, column=0, pady=5, padx=5)
        exam_scores_entry = tk.Entry(add_student_frame, textvariable=exam_scores_var, font=(self.font_family, self.font_size), state='readonly')
        exam_scores_entry.grid(row=2, column=1, pady=5, padx=5)

        # 关联题目字段，默认设置为空列表
        exam_questions_var = tk.StringVar(value="[]")
        tk.Label(add_student_frame, text="关联题目（初始为空列表，可后续修改）：", font=(self.font_family, self.font_size), bg=self.label_bg_color).grid(row=3, column=0, pady=5, padx=5)
        exam_questions_entry = tk.Entry(add_student_frame, textvariable=exam_questions_var, font=(self.font_family, self.font_size), state='readonly')
        exam_questions_entry.grid(row=3, column=1, pady=5, padx=5)

        # 提交按钮
        submit_button = tk.Button(add_student_frame, text="提交", font=(self.font_family, self.font_size),
                                  bg=self.button_bg_color, fg=self.button_fg_color,
                                  command=lambda: self.submit_add_student(name_entry.get(),
                                                                          birth_date_entry.get_date(),
                                                                          exam_scores_var.get(),
                                                                          exam_questions_var.get()))
        submit_button.grid(row=4, column=0, columnspan=2, pady=10)

    def submit_add_student(self, name, birth_date, exam_scores, exam_questions):
        """
        提交新增学生信息到数据库的具体处理方法，优化了操作反馈及参数处理
        """
        try:
            student_info = {
                "name": name,
                "birth_date": birth_date,
                "exam_scores": ast.literal_eval(exam_scores),  # 更安全地将字符串形式的列表转换为实际列表
                "exam_questions": ast.literal_eval(exam_questions)  # 更安全地将字符串形式的列表转换为实际列表
            }
            result, msg = self.database_manager.add_student(student_info)
            if result:
                messagebox.showinfo("提示", "学生信息添加成功！你可以继续添加其他学生或者查看已添加学生信息。")
            else:
                messagebox.showerror("错误", msg)
        except ValueError:
            messagebox.showerror("错误", "考试成绩或关联题目字段输入的格式不正确，请检查输入内容是否符合列表格式要求")

    def add_student_file(self):
        """
        通过文件导入的方式新增学生信息，支持常见的文件格式（如CSV、Excel等），添加了文件格式提示等优化及细化错误处理逻辑
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            if file_path.endswith('.csv') or file_path.endswith('.xlsx'):
                data = self.read_student_data_from_file(file_path)
                if data:
                    for student_info in data:
                        result, msg = self.database_manager.add_student(student_info)
                        if not result:
                            if "输入的数据格式有误" in msg:
                                messagebox.showerror("错误", f"学生信息数据格式不符合要求，请检查文件内容，具体错误: {msg}")
                            else:
                                messagebox.showerror("错误", f"向数据库添加学生信息失败，请查看相关日志或终端输出，错误信息: {msg}")
                    messagebox.showinfo("提示", "学生信息添加成功！")
                else:
                    messagebox.showwarning("警告", "读取学生数据文件失败，可能是文件内容格式不符合要求，请检查文件内容格式是否正确")
            else:
                messagebox.showwarning("警告", "不支持的文件格式，请选择.csv或.xlsx文件")
        else:
            messagebox.showwarning("警告", "未选择任何文件，请重新操作")

    def read_student_data_from_file(self, file_path):
        """
        从文件中读取学生数据，支持CSV和Excel格式
        """
        if file_path.endswith('.csv'):
            data = []
            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        row['birth_date'] = date.fromisoformat(row['birth_date'])
                        row['exam_scores'] = [] if row['exam_scores'] == "" else ast.literal_eval(row['exam_scores'])
                        row['exam_questions'] = [] if row['exam_questions'] == "" else ast.literal_eval(row['exam_questions'])
                        data.append(row)
                    except ValueError:
                        continue
            return data
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
            data = df.to_dict('records')
            for d in data:
                try:
                    d['birth_date'] = date.fromisoformat(d['birth_date'])
                    d['exam_scores'] = [] if d['exam_scores'] == "" else ast.literal_eval(d['exam_scores'])
                    d['exam_questions'] = [] if d['exam_questions'] == "" else ast.literal_eval(d['exam_questions'])
                except ValueError:
                    continue
            return data
        return []

    def update_student_form(self):
        """
        通过表单方式修改学生信息，先查找学生再展示可修改的字段进行修改，添加了输入提示及验证等优化
        """
        student_name = simpledialog.askstring("修改学生信息", "请输入要修改的学生的姓名：")
        if student_name:
            student_data = self.database_manager.get_student_data()
            target_student = None
            for student in student_data:
                if student.name == student_name:
                    target_student = student
                    break
            if target_student:
                update_student_frame = tk.Frame(self.root, bg=self.label_bg_color)
                update_student_frame.pack(pady=20, padx=20)

                # 姓名输入框（显示当前姓名，可修改）
                name_label = tk.Label(update_student_frame, text="姓名：", font=(self.font_family, self.font_size), bg=self.label_bg_color)
                name_label.grid(row=0, column=0, pady=5, padx=5)
                name_entry = tk.Entry(update_student_frame, font=(self.font_family, self.font_size))
                name_entry.insert(0, target_student.name)
                name_entry.grid(row=0, column=1, pady=5, padx=5)
                name_tooltip = ttk.Tooltip(name_label, "请输入修改后的学生姓名，长度在1-20个字符之间", bootstyle="light")

                # 出生日期输入框（显示当前出生日期，可修改，使用日期选择组件）
                birth_date_label = tk.Label(update_student_frame, text="出生日期：", font=(self.font_family, self.font_size), bg=self.label_bg_color)
                birth_date_label.grid(row=1, column=0, pady=5, padx=5)
                from tkcalendar import DateEntry
                birth_date_entry = DateEntry(update_student_frame, font=(self.font_family, self.font_size), width=12, background='darkblue',
                                             foreground='white', borderwidth=2)
                birth_date_entry.set_date(target_student.birth_date)
                birth_date_entry.grid(row=1, column=1, pady=5, padx=5)
                birth_date_tooltip = ttk.Tooltip(birth_date_label, "请选择合法的日期格式（YYYY-MM-DD）进行修改", bootstyle="light")
                def validate_birth_date(event):
                    try:
                        birth_date_entry.get_date()
                    except ValueError:
                        messagebox.showerror("错误", "请输入正确的日期格式（YYYY-MM-DD）")
                birth_date_entry.bind("<FocusOut>", validate_birth_date)

                # 提交按钮
                submit_button = tk.Button(update_student_frame, text="提交", font=(self.font_family, self.font_size),
                                          bg=self.button_bg_color, fg=self.button_fg_color,
                                          command=lambda: self.submit_update_student(target_student.id,
                                                                                    name_entry.get(),
                                                                                    birth_date_entry.get_date()))
                submit_button.grid(row=2, column=0, columnspan=2, pady=10)
            else:
                messagebox.showerror("错误", f"未找到姓名为 {student_name} 的学生，请检查输入是否正确")
        else:
            messagebox.showwarning("警告", "未输入学生姓名，无法进行修改操作，请重新输入")

    def submit_update_student(self, student_id, name, birth_date):
        """
        提交修改后的学生信息到数据库的具体处理方法，优化了操作反馈
        """
        student_info = {
            "id": student_id,
            "name": name,
            "birth_date": birth_date
        }
        result, msg = self.database_manager.update_student(student_info)
        if result:
            messagebox.showinfo("提示", "学生信息修改成功！你可以继续修改其他学生信息或者查看已修改后的学生数据。")
        else:
            messagebox.showerror("错误", msg)

    def update_student_file(self):
        """
        通过文件导入的方式修改学生信息（示例可覆盖原数据等逻辑，可按需完善），添加了文件格式提示等优化
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            if file_path.endswith('.csv') or file_path.endswith('.xlsx'):
                data = self.read_student_data_from_file(file_path)
                if data:
                    for student_info in data:
                        result, msg = self.database_manager.update_student(student_info)
                        if not result:
                            messagebox.showerror("错误", msg)
                    messagebox.showinfo("提示", "学生信息修改成功！")
                else:
                    messagebox.showwarning("提示", "读取学生数据文件失败，请检查文件内容格式是否正确")
            else:
                messagebox.showwarning("警告", "不支持的文件格式，请选择.csv或.xlsx文件")
        else:
            messagebox.showwarning("警告", "未选择任何文件，请重新操作")

    def add_exam_file(self):
        """
        通过文件导入的方式新增考试信息，支持常见文件格式（如CSV、Excel等），添加操作提示等优化
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            if file_path.endswith('.csv') or file_path.endswith('.xlsx'):
                data = self.read_exam_data_from_file(file_path)
                if data:
                    for exam_info in data:
                        result, msg = self.database_manager.add_exam(exam_info)
                        if not result:
                            messagebox.showerror("错误", msg)
                    messagebox.showinfo("提示", "考试信息添加成功！")
                else:
                    messagebox.showwarning("警告", "读取考试数据文件失败，请检查文件内容格式是否正确")
            else:
                messagebox.showwarning("警告", "不支持的文件格式，请选择.csv或.xlsx文件")
        else:
            messagebox.showwarning("警告", "未选择任何文件，请重新操作")

    def read_exam_data_from_file(self):
        """
        从文件中读取考试数据，支持CSV和Excel格式
        """
        file_path = filedialog.askopenfilename()
        if file_path.endswith('.csv'):
            data = []
            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append(row)
            return data
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
            return df.to_dict('records')
        return []

    def         add_question_file(self):
        """
        通过文件导入的方式新增题目信息，支持常见文件格式（如CSV、Excel等），添加操作提示及图片相关处理等优化
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            if file_path.endswith('.csv') or file_path.endswith('.xlsx'):
                data = self.read_question_data_from_file(file_path)
                if data:
                    for question_info in data:
                        # 处理题目图片（如果有图片路径相关信息）
                        image_path = question_info.get('image_path')
                        if image_path:
                            try:
                                img = Image.open(image_path)
                                img.thumbnail((200, 200))  # 可根据需要调整显示大小
                                question_info['image'] = ImageTk.PhotoImage(img)
                            except:
                                messagebox.showerror("错误", f"加载题目图片 {image_path} 失败，请检查图片文件是否存在及格式是否正确")
                                continue
                        result, msg = self.database_manager.add_question(question_info)
                        if not result:
                            messagebox.showerror("错误", msg)
                    messagebox.showinfo("提示", "题目信息添加成功！")
                else:
                    messagebox.showwarning("警告", "读取题目数据文件失败，请检查文件内容格式是否正确")
            else:
                messagebox.showwarning("警告", "不支持的文件格式，请选择.csv或.xlsx文件")
        else:
            messagebox.showwarning("警告", "未选择任何文件，请重新操作")

    def read_question_data_from_file(self):
        """
        从文件中读取题目数据，支持CSV和Excel格式
        """
        file_path = filedialog.askopenfilename()
        if file_path.endswith('.csv'):
            data = []
            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append(row)
            return data
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
            return df.to_dict('records')
        return []

    def add_tag_file(self):
        """
        通过文件导入的方式新增标签信息，支持常见文件格式（如CSV、Excel等），添加操作提示等优化
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            if file_path.endswith('.csv') or file_path.endswith('.xlsx'):
                data = self.read_tag_data_from_file(file_path)
                if data:
                    for tag_info in data:
                        result, msg = self.database_manager.add_tag(tag_info)
                        if not result:
                            messagebox.showerror("错误", msg)
                    messagebox.showinfo("提示", "标签信息添加成功！")
                else:
                    messagebox.showwarning("警告", "读取标签数据文件失败，请检查文件内容格式是否正确")
            else:
                messagebox.showwarning("警告", "不支持的文件格式，请选择.csv或.xlsx文件")
        else:
            messagebox.showwarning("警告", "未选择任何文件，请重新操作")

    def read_tag_data_from_file(self):
        """
        从文件中读取标签数据，支持CSV和Excel格式
        """
        file_path = filedialog.askopenfilename()
        if file_path.endswith('.csv'):
            data = []
            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append(row)
            return data
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
            return df.to_dict('records')
        return []

    def update_exam_file(self):
        """
        通过文件导入的方式修改考试信息（示例可覆盖原数据等逻辑，可按需完善），添加操作提示等优化
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            if file_path.endswith('.csv') or file_path.endswith('.xlsx'):
                data = self.read_exam_data_from_file(file_path)
                if data:
                    for exam_info in data:
                        result, msg = self.database_manager.update_exam(exam_info)
                        if not result:
                            messagebox.showerror("错误", msg)
                    messagebox.showinfo("提示", "考试信息修改成功！")
                else:
                    messagebox.showwarning("提示", "读取考试数据文件失败，请检查文件内容格式是否正确")
            else:
                messagebox.showwarning("警告", "不支持的文件格式，请选择.csv或.xlsx文件")
        else:
            messagebox.showwarning("警告", "未选择任何文件，请重新操作")

    def update_question_file(self):
        """
        通过文件导入的方式修改题目信息（示例可覆盖原数据等逻辑，可按需完善），添加操作提示等优化
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            if file_path.endswith('.csv') or file_path.endswith('.xlsx'):
                data = self.read_question_data_from_file(file_path)
                if data:
                    for question_info in data:
                        result, msg = self.database_manager.update_question(question_info)
                        if not result:
                            messagebox.showerror("错误", msg)
                    messagebox.showinfo("提示", "题目信息修改成功！")
                else:
                    messagebox.showwarning("提示", "读取题目数据文件失败，请检查文件内容格式是否正确")
            else:
                messagebox.showwarning("警告", "不支持的文件格式，请选择.csv或.xlsx文件")
        else:
            messagebox.showwarning("警告", "未选择任何文件，请重新操作")

    def update_tag_file(self):
        """
        通过文件导入的方式修改标签信息（示例可覆盖原数据等逻辑，可按需完善），添加操作提示等优化
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            if file_path.endswith('.csv') or file_path.endswith('.xlsx'):
                data = self.read_tag_data_from_file(file_path)
                if data:
                    for tag_info in data:
                        result, msg = self.database_manager.update_tag(tag_info)
                        if not result:
                            messagebox.showerror("错误", msg)
                    messagebox.showinfo("提示", "标签信息修改成功！")
                else:
                    messagebox.showwarning("提示", "读取标签数据文件失败，请检查文件内容格式是否正确")
            else:
                messagebox.showwarning("警告", "不支持的文件格式，请选择.csv或.xlsx文件")
        else:
            messagebox.showwarning("警告", "未选择任何文件，请重新操作")

    def delete_student(self):
        """
        根据输入的学生姓名删除学生信息，优化了操作反馈
        """
        student_name = simpledialog.askstring("删除学生", "请输入要删除的学生的姓名：")
        if student_name:
            result, msg = self.database_manager.delete_student(student_name)
            if result:
                messagebox.showinfo("提示", "学生信息删除成功！")
            else:
                messagebox.showerror("错误", msg)
        else:
            messagebox.showwarning("警告", "未输入学生姓名，无法进行删除操作，请重新输入")

    def delete_exam(self):
        """
        根据输入的考试编号删除考试信息，优化了操作反馈
        """
        exam_id = simpledialog.askstring("删除考试", "请输入要删除的考试的编号：")
        if exam_id:
            result, msg = self.database_manager.delete_exam(exam_id)
            if result:
                messagebox.showinfo("提示", "考试信息删除成功！")
            else:
                messagebox.showerror("错误", "未找到对应编号的考试信息，请检查输入是否正确")
        else:
            messagebox.showwarning("警告", "未输入考试编号，无法进行删除操作，请重新输入")

    def delete_question(self):
        """
        根据输入的题目编号删除题目信息，优化了操作反馈
        """
        question_id = simpledialog.askstring("删除题目", "请输入要删除的题目的编号：")
        if question_id:
            result, msg = self.database_manager.delete_question(question_id)
            if result:
                messagebox.showinfo("提示", "题目信息删除成功！")
            else:
                messagebox.showerror("错误", "未找到对应编号的题目信息，请检查输入是否正确")
        else:
            messagebox.showwarning("警告", "未输入题目编号，无法进行删除操作，请重新输入")

    def delete_tag(self):
        """
        根据输入的标签内容删除标签信息，优化了操作反馈
        """
        tag_content = simpledialog.askstring("删除标签", "请输入要删除的标签的内容：")
        if tag_content:
            result, msg = self.database_manager.delete_tag(tag_content)
            if result:
                messagebox.showinfo("提示", "标签信息删除成功！")
            else:
                messagebox.showerror("错误", "未找到对应内容的标签信息，请检查输入是否正确")
        else:
            messagebox.showwarning("警告", "未输入标签内容，无法进行删除操作，请重新输入")

    def view_student_data(self):
        """
        查看学生数据并展示在消息框中，展示更详细合理的信息格式，添加了界面布局及展示优化
        """
        student_data = self.database_manager.get_student_data()
        if student_data:
            data_text = ""
            for s in student_data:
                data_text += f"姓名: {s.name}, 出生日期: {s.birth_date.strftime('%Y-%m-%d')}, 年龄: {s.age}\n"
                data_text += "考试成绩记录:\n"
                for score in s.exam_scores:
                    data_text += f"    考试编号: {score.exam.exam_number}, 成绩: {score.score}\n"
                data_text += "关联题目:\n"
                for question in s.exam_questions:
                    data_text += f"    考试编号: {question.question.question_number}, 所属章节: {question.question.section}\n"
            messagebox.showinfo("学生数据", data_text)
        else:
            messagebox.showinfo("学生数据", "暂无学生数据记录")

    def view_exam_data(self):
        """
        查看考试数据并展示在消息框中，添加了展示优化
        """
        exam_data = self.database_manager.get_exam_data()
        if exam_data:
            data_text = ""
            for e in exam_data:
                data_text += f"考试编号: {e.exam_number}, 组织: {e.organization}, 组织时间: {e.time}\n"
                data_text += "参与学生:\n"
                for student in e.students:
                    data_text += f"    学生姓名: {student.name}\n"
                data_text += "包含题目:\n"
                for question in e.questions:
                    data_text += f"    题目编号: {question.question_number}, 所属章节: {question.section}\n"
            messagebox.showinfo("考试数据", data_text)
        else:
            messagebox.showinfo("考试数据", "暂无考试数据记录")

    def view_question_data(self):
        """
        查看题目数据并展示在消息框中，添加了图片展示相关处理及展示优化
        """
        question_data = self.database_manager.get_question_data()
        if question_data:
            data_text = ""
            for q in question_data:
                data_text += f"题目编号: {q.question_number}, 所属章节: {q.section}, 难度: {q.difficulty}\n"
                if q.image_path:
                    try:
                        img = Image.open(q.image_path)
                        img.thumbnail((200, 200))
                        img_tk = ImageTk.PhotoImage(img)
                        tk.Label(None, image=img_tk).pack()  # 简单示例展示图片，实际需合理布局在界面中
                        data_text += "（包含图片展示）\n"
                    except:
                        data_text += "（图片加载失败）\n"
                data_text += "关联考试:\n"
                for exam in q.exams:
                    data_text += f"    考试编号: {exam.exam_number}\n"
                data_text += "关联学生:\n"
                for student in q.students:
                    data_text += f"    学生姓名: {student.name}\n"
            messagebox.showinfo("题目数据", data_text)
        else:
            messagebox.showinfo("题目数据", "暂无题目数据记录")

    def view_tag_data(self):
        """
        查看标签数据并展示在消息框中，添加了展示优化
        """
        tag_data = self.database_manager.get_tag_data()
        if tag_data:
            data_text = ""
            for t in tag_data:
                data_text += f"标签内容: {t.content}\n"
                data_text += "关联题目:\n"
                for question in t.questions:
                    data_text += f"    题目编号: {question.question_number}\n"
                data_text += "关联考试:\n"
                for exam in t.exams:
                    data_text += f"    考试编号: {exam.exam_number}\n"
            messagebox.showinfo("标签数据", data_text)
        else:
            messagebox.showinfo("标签数据", "暂无标签数据记录")

    def analyze_student_by_exam(self):
        """
        按考试分析学生数据（示例，可进一步完善具体分析逻辑），添加了提示信息
        """
        messagebox.showinfo("提示", "此功能可按考试维度分析学生数据，目前功能正在完善中，暂仅提供简单提示示例。")

    def analyze_student_by_tag(self):
        """
        按标签分析学生数据（示例，可进一步完善具体分析逻辑），添加了提示信息
        """
        messagebox.showinfo("提示", "此功能可按标签维度分析学生数据，目前功能正在完善中，暂仅提供简单提示示例。")

    def analyze_student_by_question(self):
        """
        按题目分析学生数据（示例，可进一步完善具体分析逻辑），添加了提示信息
        """
        messagebox.showinfo("提示", "此功能可按题目维度分析学生数据，目前功能正在完善中，暂仅提供简单提示示例。")


if __name__ == "__main__":
    database_manager = DatabaseManager()
    gui = GUI(database_manager)
    gui.run()
