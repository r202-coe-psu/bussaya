import re
import subprocess





'''

โค้ดนี้เป็นส่วนหนึ่งของการตรวจสอบใบรับรองในไฟล์ PDF โดยใช้ OpenSSL

ฟังก์ชันหลัก:
  - extract_certificates(pdf_path, ca_cert_path): ดึงลายเซ็นจากไฟล์ PDF, ตรวจสอบ, และดึงชื่อผู้เซ็น

การตรวจสอบใบรับรองจะไม่บันทึกไฟล์ข้อมูล แต่จะทำการเขียนลงในหน่วยความจำเท่านั้น

ข้อจำกัด:
  - ไม่สามารถตรวจสอบ hash ได้
  - ไม่สามารถตรวจสอบว่าไฟล์ PDF ถูกเปลี่ยนแปลงหรือไม่

'''



def run_openssl(command, input_data=None, text_output=True):
    """เรียกใช้งาน OpenSSL และคืนค่าผลลัพธ์"""
    try:
        result = subprocess.run(
            command,
            input=input_data,
            capture_output=True,
            check=True,
            text=text_output
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        '''   
            #####debug code
        print("❌ OpenSSL Error:", e.stderr)
        '''
        return None


def extract_certificate_from_signature(signature_binary):
    """ดึงใบรับรองทั้งหมดจากลายเซ็น (PKCS#7) โดยไม่ต้องใช้ไฟล์"""
    command = ["openssl", "pkcs7", "-inform", "DER", "-print_certs"]

    # ใช้ subprocess เพื่อส่งข้อมูลเข้า OpenSSL ผ่าน stdin และรับผลลัพธ์จาก stdout
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=signature_binary)

    if process.returncode != 0:
        '''
        #####debug code
        print("OpenSSL Error:", stderr.decode())
        '''
        return None  # คืนค่า None ถ้าผิดพลาด

    # แยกใบรับรองทั้งหมดในผลลัพธ์
    certs = stdout.decode().split("-----END CERTIFICATE-----")
    certs = [cert.strip() + "\n-----END CERTIFICATE-----" for cert in certs if "-----BEGIN CERTIFICATE-----" in cert]
    return certs  # คืนค่าใบรับรองทั้งหมดในรูปแบบลิสต์

def verify_certificate(ca_cert_path, cert_pem):
    """ตรวจสอบใบรับรองกับ CA ที่กำหนด โดยไม่ต้องใช้ไฟล์ และไม่สนใจวันหมดอายุ"""

    command = ["openssl", "verify", "-CAfile", ca_cert_path, "-no_check_time"]
    # ใช้ subprocess เพื่อส่งข้อมูลใบรับรองเข้า OpenSSL ผ่าน stdin
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=cert_pem.encode())

    if process.returncode != 0:
        '''
        #####debug code
        print("OpenSSL Verify Error:", stderr.decode())
        '''
        return False  # คืนค่า False ถ้าการตรวจสอบล้มเหลว

    return "OK" in stdout.decode()  # คืนค่า True ถ้าการตรวจสอบสำเร็จ

def extract_certificates(pdf_file, ca_cert_path):
    """ดึงลายเซ็นจากไฟล์ PDF, ตรวจสอบ, และดึงเฉพาะ CN จาก subject และ issuer"""
    try:
        data = pdf_file
        if isinstance(data, str):
            data = data.encode('utf-8')
    except Exception as e:
        '''
        #####debug code
        # print(f"❌ ไม่สามารถอ่านไฟล์ PDF: {e}")
        '''
        return []

    # ค้นหาลายเซ็นในไฟล์ PDF
    matches = re.findall(rb"/(?:Contents|ByteRange|Signature|Sig|Cert|SignedData|PKCS7)\s*<([0-9A-Fa-f]+)>", data)
    if not matches:
        '''
        #####debug code
        # print("❌ ไม่พบลายเซ็นในไฟล์ PDF")
        '''
        return []

    verified_signatures = []  # เก็บเฉพาะ CN ทั้งหมด
    excluded_cns = ['Thai University Consortium Certification Authority', 'Prince of Songkla University Certification Authority']

    for i, hex_data in enumerate(matches):
        try:
            signature_binary = bytes.fromhex(hex_data.decode())

            # ดึงใบรับรองทั้งหมดจากลายเซ็น
            certs = extract_certificate_from_signature(signature_binary)
            if not certs:
                '''
                #####debug code
                # print(f"⚠️ ไม่สามารถดึงใบรับรองจากลายเซ็นที่ {i+1}")
                '''
                continue

            for j, cert_pem in enumerate(certs):
                # ตรวจสอบใบรับรองกับ CA
                is_verified = verify_certificate(ca_cert_path, cert_pem)

                '''      
                #####debug code          
                if not is_verified:
                    print(f"❌ ใบรับรองที่ {j+1} ของลายเซ็นที่ {i+1} ไม่ผ่านการตรวจสอบ")

                print(f"✅ ใบรับรองที่ {j+1} ของลายเซ็นที่ {i+1} {'ผ่านการตรวจสอบ' if is_verified else 'ไม่ผ่านการตรวจสอบ'}")
                '''


                # ดึงเฉพาะ CN จาก subject และ issuer
                subject_cn_match = re.search(r"CN=([^,\n]+)", cert_pem)
                issuer_cn_match = re.search(r"Issuer:.*?CN=([^,\n]+)", cert_pem)

                subject_cn = subject_cn_match.group(1).strip() if subject_cn_match else None
                issuer_cn = issuer_cn_match.group(1).strip() if issuer_cn_match else None

                # เพิ่มเฉพาะ CN ลงในลิสต์ (ยกเว้น CN ที่ไม่ต้องการ)
                if subject_cn and subject_cn not in excluded_cns and is_verified:
                    verified_signatures.append(subject_cn)
                if issuer_cn and issuer_cn not in excluded_cns and is_verified:
                    verified_signatures.append(issuer_cn)

            '''
                # แสดงข้อมูลใบรับรอง
                print(f"   - ข้อมูลใบรับรองที่ {j+1} ของลายเซ็นที่ {i+1}:")
                print(f"       Subject CN: {subject_cn}")
                print(f"       Issuer CN: {issuer_cn}")
                print(f"       Verified: {'Yes' if is_verified else 'No'}")
            print(verified_signatures)
            '''

        except Exception as e:

            '''
            #####debug code
            # print(f"⚠️ เกิดข้อผิดพลาดในการประมวลผลลายเซ็นที่ {i+1}: {e}")
            '''

            pass

    return verified_signatures

'''
    ตัวอย่างการใช้งาน:

    cert_path = 'trust_cert.pem'  # ไฟล์ CA ของคุณ
    pdf_path = 'your_pdf.pdf'  # ไฟล์ PDF ของคุณ

    verified_signers = extract_certificates(pdf_path, cert_path)
    print("ชื่อผู้เซ็นที่ผ่านการตรวจสอบ:", verified_signers)
'''
