import datetime
import time
from ctypes import windll, Structure, byref, pointer, c_wchar_p, \
    c_ulonglong, pointer, WinError, create_string_buffer
from ctypes.wintypes import LPWSTR, DWORD, BOOL, FILETIME, LPVOID

GENERIC_READ = 0x80000000 # 0
FILE_FLAG_WRITE_THROUGH = 0x80000000
FILE_SHARE_MODE = 0x00000000
FILE_BEGIN = 0
SECURITY_ATTRIBUTES = 0
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 128

# Time
EPOCH_AS_FILETIME = 116444736000000000
HUNDREDS_OF_NANOSECONDS = 10000000

root = c_wchar_p(u"C:\\")
filename = 'C:\\Users\\Nutzer\\Desktop\\ElectionService.txt'

hFile = windll.kernel32.CreateFileW(filename, 
        GENERIC_READ, 
        FILE_SHARE_MODE, 
        SECURITY_ATTRIBUTES, 
        OPEN_EXISTING, 
        FILE_ATTRIBUTE_NORMAL, 
        None
)

class WIN32_FILE_ATTRIBUTE_DATA(Structure):
    _fields_ = [("dwFileAttributes", DWORD),
                ("ftCreationTime", FILETIME),
                ("ftLastAccessTime", FILETIME),
                ("ftLastWriteTime", FILETIME),
                ("nFileSizeHigh", DWORD),
                ("nFileSizeLow", DWORD)]

class _SECURITY_ATTRIBUTES(Structure): # not used
    _fields_ = [("nLength", DWORD),
                ("lpSecurityDescriptor", LPVOID),
                ("bInheritHandle", BOOL)]

def filetime_to_dt(ft): 
    us = (ft - EPOCH_AS_FILETIME) // 10 
    return datetime.datetime.fromtimestamp((ft - EPOCH_AS_FILETIME) / HUNDREDS_OF_NANOSECONDS)

def convert_fileTime(high, low):
    return ((high << 32) + low)

def output():
    print("\nUsing: Win32 C++-Function GetDiskFreeSpaceW with Python")
    print("Sectors per Cluster          ", sectorsPerCluster.value)
    print("Bytes per Sectors            ", bytesPerSector)
    print("Bytes per Cluster            ", bytesPerCluster)
    print("Sum of free Clusters         ", numberOfFreeClusters.value)
    print("Sum of Clusters              ", totalNumberOfClusters.value)
    print("Total Sectors                ", quad_sum)

    print("\nUsing: Win32 C++-Function GetFileAttributesExW with WIN32_FILE_ATTRIBUTE_DATA structure with Python")
    print("Given File:                 ", filename)
    print("File-Attribute              ", wfad.dwFileAttributes , "- FILE_ATTRIBUTE_ARCHIVE(0x20) if 32, check: File Attribute Constants")
    print("CreationTime                ", filetime_to_dt(convert_fileTime(wfad.ftCreationTime.dwHighDateTime, wfad.ftCreationTime.dwLowDateTime)))
    print("LastAccessTime              ", filetime_to_dt(convert_fileTime(wfad.ftLastAccessTime.dwHighDateTime, wfad.ftLastAccessTime.dwLowDateTime)))
    print("LastWriteTime               ", filetime_to_dt(convert_fileTime(wfad.ftLastWriteTime.dwHighDateTime, wfad.ftLastWriteTime.dwLowDateTime)))

    if (wfad.nFileSizeHigh == 0):
        print("FileSizeHigh                ", "is ",wfad.nFileSizeHigh , ", DWORD < 64 Bit")
        print("FileSizeLow                 ", wfad.nFileSizeLow)
        print("Free File Slack             ", int(bytesPerCluster - wfad.nFileSizeLow))
        print("RAM Slack:                  ", int(bytesPerSector - tmpFileSize))
        print("Drive Slack                 ", int(freeSectors * bytesPerSector))
        print("Written Sectors:            ", writtenSectors)
        print("Free Sectors:               ", freeSectors)
    
        print(data_content)
    else:
        raise NotImplementedError


# Get Clusterinformation
sectorsPerCluster = c_ulonglong(0)
bytesPerSector = c_ulonglong(0)
numberOfFreeClusters = c_ulonglong(0)
totalNumberOfClusters = c_ulonglong(0)

# Use GetDiskFreeSpaceW
if not (windll.kernel32.GetDiskFreeSpaceW(root, pointer(sectorsPerCluster), pointer(bytesPerSector),
    pointer(numberOfFreeClusters), pointer(totalNumberOfClusters))):
    raise WinError()

quad_sum = totalNumberOfClusters.value * sectorsPerCluster.value
bytesPerCluster = int(bytesPerSector.value * sectorsPerCluster.value)
bytesPerSector = bytesPerSector.value

wfad = WIN32_FILE_ATTRIBUTE_DATA()
GetFileExInfoStandard = 0

# Use GetFileAttributesExW
windll.kernel32.GetFileAttributesExW(LPWSTR(filename), GetFileExInfoStandard, byref(wfad))

# Calculate written Sectors and free Spaces
writtenSectors, tmpFileSize = 0, wfad.nFileSizeLow
while(tmpFileSize > bytesPerSector):
    tmpFileSize = int(tmpFileSize - bytesPerSector)
    writtenSectors += 1
freeSectors = sectorsPerCluster.value - writtenSectors - 1

# Set Filepointer, Lock File, Read File, Unlock File
pointer = windll.kernel32.SetFilePointer(filename, quad_sum, None, FILE_BEGIN)
if (pointer==0):
    raise WinError()

windll.kernel32.LockFile(filename, pointer, 0, int(bytesPerCluster - wfad.nFileSizeLow), 0)

bytesRead = DWORD(0)
data = create_string_buffer(int(bytesPerCluster - wfad.nFileSizeLow))
if not windll.kernel32.ReadFile(hFile, data, 4096, byref(bytesRead), None):
    raise WinError()
data_content = data.value[0:4096]

windll.kernel32.UnlockFile(filename, pointer, 0, int(bytesPerCluster - wfad.nFileSizeLow), 0)



if __name__ == "__main__":
    output()