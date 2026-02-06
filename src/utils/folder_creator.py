from pathlib import Path

def create_folders(*paths):
    """
    Hàm tạo thư mục cho bao nhiêu đường dẫn cũng được.
    Truyền vào: Các chuỗi đường dẫn (string) hoặc đối tượng Path.
    """
    for p in paths:
        path_obj = Path(p)
        
        # Nếu p là đường dẫn đến FILE (có đuôi .png, .csv...) thì lấy folder cha
        # Nếu p chỉ là đường dẫn FOLDER thì tạo trực tiếp folder đó
        if path_obj.suffix: 
            target_dir = path_obj.parent
        else:
            target_dir = path_obj
            
        target_dir.mkdir(parents=True, exist_ok=True)
