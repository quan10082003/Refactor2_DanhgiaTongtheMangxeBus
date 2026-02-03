2# Lớp học Clean Code: Review chi tiết

Chào em, thầy đã xem qua code của em. Thầy ghi nhận sự nỗ lực rất lớn của em trong việc áp dụng các kiến thức nâng cao như `dataclass` hay `ABC`. Tư duy chia module của em cũng rất sáng sủa.

Tuy nhiên, "Clean Code" không chỉ là chạy được, mà là code phải "kể chuyện" cho người đọc. Dưới đây là những điểm thầy muốn em lưu ý để code của mình trở nên chuyên nghiệp hơn (Professional & Pythonic).

---

## 1. Đặt tên (Naming) - Hãy để tên gọi nói lên ý nghĩa

Trong file [src/od_mask/core_class.py](file:///d:/CONG_VIEC_VTS/01-WORKS/02-MATSIM/01-CHAM-DIEM-MANG-LUOI-XE-BUS/03-Code/2-PERSONAL/v3_Danh_Gia_Tong_The_MangLuoiXeBus/src/od_mask/core_class.py):

```python
# Hiện tại:
class GenerateZoneMethodInterFace(ABC): ...
```
**Nhận xét:**
*   Em đang viết hoa chữ `F` trong `InterFace`. Trong Python, chúng ta dùng quy tắc **PascalCase** cho tên class (viết hoa chữ cái đầu mỗi từ), nhưng [Interface](file:///d:/CONG_VIEC_VTS/01-WORKS/02-MATSIM/01-CHAM-DIEM-MANG-LUOI-XE-BUS/03-Code/2-PERSONAL/v3_Danh_Gia_Tong_The_MangLuoiXeBus/src/od_mask/core_class.py#12-19) là một từ đơn, nên viết là [Interface](file:///d:/CONG_VIEC_VTS/01-WORKS/02-MATSIM/01-CHAM-DIEM-MANG-LUOI-XE-BUS/03-Code/2-PERSONAL/v3_Danh_Gia_Tong_The_MangLuoiXeBus/src/od_mask/core_class.py#12-19) chứ không phải `InterFace`.
*   Tên class hơi dài. Nếu class này nằm trong module `zone`, em có thể cân nhắc `ZoneGenerator` hoặc `ZoneGenerationStrategy` (nếu dùng Strategy Pattern). Nhưng giữ tên hiện tại cũng được nếu nó rõ nghĩa, chỉ cần sửa lại Case.

**Sửa lại:**
```python
class GenerateZoneMethodInterface(ABC): ...
```

---

## 2. Kiểu dữ liệu (Data Interface) - Hãy dùng đúng kiểu cho đúng việc

Trong [src/domain/point.py](file:///d:/CONG_VIEC_VTS/01-WORKS/02-MATSIM/01-CHAM-DIEM-MANG-LUOI-XE-BUS/03-Code/2-PERSONAL/v3_Danh_Gia_Tong_The_MangLuoiXeBus/src/domain/point.py) và [src/network/core_class.py](file:///d:/CONG_VIEC_VTS/01-WORKS/02-MATSIM/01-CHAM-DIEM-MANG-LUOI-XE-BUS/03-Code/2-PERSONAL/v3_Danh_Gia_Tong_The_MangLuoiXeBus/src/network/core_class.py):

```python
# Hiện tại:
class Point:
    x: str
    y: str

class Link:
    length: str
```
**Bài giảng:**
*   Tại sao em lại lưu tọa độ và chiều dài là `str` (chuỗi)? Máy tính cần con số để tính toán khoảng cách, tìm đường.
*   Nếu để `str`, mỗi lần cần cộng trừ nhân chia, chương trình phải làm thêm bước "phiên dịch" (`float(x)`), vừa chậm vừa làm code bị rác.
*   Đừng bao giờ tin tưởng dữ liệu đầu vào (ví dụ từ XML) sẽ luôn là string mãi mãi. Hãy convert nó sang kiểu dữ liệu chuẩn (`float`, [int](file:///d:/CONG_VIEC_VTS/01-WORKS/02-MATSIM/01-CHAM-DIEM-MANG-LUOI-XE-BUS/03-Code/2-PERSONAL/v3_Danh_Gia_Tong_The_MangLuoiXeBus/src/domain/point.py#3-7)) ngay từ "cửa khẩu" (lúc đọc file).

**Sửa lại:**
```python
class Point:
    x: float
    y: float

class Link:
    length: float
```
*(Đương nhiên, em phải cập nhật logic đọc file XML để ép kiểu float ngay khi parse)*.

---

## 3. Abstract Base Class - Dùng công cụ hiện đại (Modern Python)

```python
# Hiện tại:
class GenerateZoneMethodInterFace(ABC):
    @abstractproperty
    network_path: str
```
**Bài giảng:**
*   `@abstractproperty` đã bị "khai tử" (deprecated) từ Python 3.3.
*   Cách hiện đại và chuẩn chỉ là kết hợp `@property` và `@abstractmethod`.

**Sửa lại:**
```python
class GenerateZoneMethodInterface(ABC):
    @property
    @abstractmethod
    def network_path(self) -> str:
        pass
```

---

## 4. Documentation (Docstring) - Lời tựa cho code

File [src/network/network.py](file:///d:/CONG_VIEC_VTS/01-WORKS/02-MATSIM/01-CHAM-DIEM-MANG-LUOI-XE-BUS/03-Code/2-PERSONAL/v3_Danh_Gia_Tong_The_MangLuoiXeBus/src/network/network.py) có hàm [generate_nodes_and_links_dict](file:///d:/CONG_VIEC_VTS/01-WORKS/02-MATSIM/01-CHAM-DIEM-MANG-LUOI-XE-BUS/03-Code/2-PERSONAL/v3_Danh_Gia_Tong_The_MangLuoiXeBus/src/network/network.py#8-30).
**Bài giảng:**
*   Một người mới đọc vào hàm này sẽ tự hỏi: *"network_path là đường dẫn tuyệt đối hay tương đối?", "Dict trả về key là gì, value là gì?"*.
*   Hàm của em đang "im lặng". Hãy thêm Docstring (Google Style hoặc NumPy Style).

**Ví dụ:**
```python
def generate_nodes_and_links_dict(network_path: str) -> tuple[dict[str, Node], dict[str, Link]]:
    """
    Parses the network XML file to generate dictionaries of Nodes and Links.

    Args:
        network_path (str): Absolute path to the MATSim network XML file.

    Returns:
        tuple: A tuple containing:
            - nodes_dict (dict[str, Node]): Mapping of node ID to Node object.
            - links_dict (dict[str, Link]): Mapping of link ID to Link object.
    """
    # ...
```

---

## 5. Testing - Đừng để code demo lẫn vào code thật

Đoạn `if __name__ == "__main__":` trong [network.py](file:///d:/CONG_VIEC_VTS/01-WORKS/02-MATSIM/01-CHAM-DIEM-MANG-LUOI-XE-BUS/03-Code/2-PERSONAL/v3_Danh_Gia_Tong_The_MangLuoiXeBus/src/network/network.py) rất tiện để debug, nhưng:
*   Nó chứa logic hardcode đường dẫn.
*   Nó in ra console quá nhiều.
*   **Lời khuyên:** Hãy tập thói quen viết Unit Test riêng biệt (trong thư mục `tests/`). Code logic nên "sạch", không nên chứa code chạy thử.

---

## Tổng kết bài học hôm nay

1.  **Sửa lỗi chính tả:** `InterFace` -> [Interface](file:///d:/CONG_VIEC_VTS/01-WORKS/02-MATSIM/01-CHAM-DIEM-MANG-LUOI-XE-BUS/03-Code/2-PERSONAL/v3_Danh_Gia_Tong_The_MangLuoiXeBus/src/od_mask/core_class.py#12-19).
2.  **Tư duy dữ liệu:** `str` -> `float` cho các chỉ số định lượng.
3.  **Cập nhật kiến thức:** Không dùng `@abstractproperty`.
4.  **Trách nhiệm:** Viết docstring cho hàm public.

Code em viết đã chạy được, thầy tin là nếu áp dụng những quy tắc "nhỏ" này, code của em sẽ "lớn" và chuyên nghiệp hơn rất nhiều. Cố gắng lên nhé!
