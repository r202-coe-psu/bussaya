import re
import subprocess
import tempfile
import os





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


def extract_certificate_from_signature(signature_binary, output_cert_path):
    """ดึงใบรับรองจากลายเซ็น (PKCS#7) และบันทึกเป็น PEM"""
    # กำหนดไดเรกทอรีสำหรับไฟล์ชั่วคราว
    temp_dir = os.path.join(os.getcwd(), "bussaya/certificate")
    os.makedirs(temp_dir, exist_ok=True)  # สร้างไดเรกทอรีหากยังไม่มี

    # สร้างไฟล์ชั่วคราวในไดเรกทอรีที่กำหนด
    with tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix=".der") as temp_sig_file:
        temp_sig_file.write(signature_binary)
        temp_sig_file_path = temp_sig_file.name

    # ใช้ OpenSSL เพื่อดึงใบรับรอง
    output_cert_path = os.path.join(temp_dir, output_cert_path)
    command = ["openssl", "pkcs7", "-inform", "DER", "-print_certs", "-out", output_cert_path]
    result = run_openssl(command, signature_binary, text_output=False)

    # ลบไฟล์ชั่วคราว
    os.remove(temp_sig_file_path)

    return os.path.exists(output_cert_path)


def verify_certificate(ca_cert_path, cert_path):
    """ตรวจสอบใบรับรองกับ CA ที่กำหนด"""
    command = ["openssl", "verify", "-CAfile", ca_cert_path, cert_path]
    result = run_openssl(command)
    return result and "OK" in result


def extract_certificates(pdf_file, ca_cert_path):
    """ดึงลายเซ็นจากไฟล์ PDF, ตรวจสอบ, และดึงชื่อผู้เซ็น"""
    try:
        data = pdf_file
        if isinstance(data, str):
            data = data.encode('utf-8')
    except Exception as e:
        '''   
            #####debug code
        print(f"❌ ไม่สามารถอ่านไฟล์ PDF: {e}")
        '''
        return []
    
    # ค้นหาลายเซ็นในไฟล์ PDF
    matches = re.findall(rb"/(?:Contents|ByteRange|Signature|Sig|Cert|SignedData|PKCS7)\s*<([0-9A-Fa-f]+)>", data)
    if not matches:
        '''   
            #####debug code
        print("❌ ไม่พบลายเซ็นในไฟล์ PDF")
        '''
        return []
    
    verified_signer_names = []
    temp_dir = os.path.join(os.getcwd(), "bussaya/certificate")
    os.makedirs(temp_dir, exist_ok=True)  # สร้างไดเรกทอรีหากยังไม่มี

    for i, hex_data in enumerate(matches):
        try:
            signature_binary = bytes.fromhex(hex_data.decode())
            cert_path = os.path.join(temp_dir, f"cert_{i}.pem")
            
            # ดึงใบรับรองจากลายเซ็น
            if not extract_certificate_from_signature(signature_binary, cert_path):
                '''   
                    #####debug code
                    print(f"⚠️ ไม่สามารถดึงใบรับรองจากลายเซ็นที่ {i+1}")
                '''
                continue
            '''   
                #####debug code
            print(f"🔹 พบลายเซ็นที่ {i+1}:")
            '''
            
            # ตรวจสอบใบรับรองกับ CA
            if not verify_certificate(ca_cert_path, cert_path):
                '''   
                    #####debug code
                print(f"❌ ลายเซ็นที่ {i+1} ไม่ผ่านการตรวจสอบ")
                '''
                os.remove(cert_path)
                continue
            
            #####print(f"✅ ลายเซ็นที่ {i+1} ผ่านการตรวจสอบ") debug code 
            
            # ใช้ OpenSSL เพื่อตรวจสอบลายเซ็นและดึงข้อมูล
            with tempfile.NamedTemporaryFile(delete=False, dir=temp_dir, suffix=".der") as temp_sig_file:
                temp_sig_file.write(signature_binary)
                temp_sig_file_path = temp_sig_file.name
            
            output_text = run_openssl(["openssl", "pkcs7", "-inform", "DER", "-in", temp_sig_file_path, "-print_certs", "-noout", "-text"])
            os.remove(temp_sig_file_path)
            os.remove(cert_path)
            
            '''            
            #####debug code
            if not output_text:
                print(f"⚠️ ไม่สามารถดึงข้อมูลลายเซ็นที่ {i+1}")
                continue
            '''
            
            # ดึง CN (Common Name) จากข้อมูลใบรับรอง
            cn_matches = re.findall(r"CN=([^,\n]+)", output_text)
            if cn_matches:
                signer_name = cn_matches[-1].split('/')[0]
                verified_signer_names.append(signer_name)
                # print(f"   - เซ็นโดย: {signer_name}")
            else:
                pass
                # print(f"⚠️ ไม่พบ CN ในลายเซ็นที่ {i+1}")
        
        except Exception as e:
            '''
            #####debug code
            print(f"⚠️ เกิดข้อผิดพลาดในการประมวลผลลายเซ็นที่ {i+1}: {e}")
            '''
            pass
    
    return verified_signer_names

'''
    ตัวอย่างการใช้งาน:

    cert_path = 'trust_cert.pem'  # ไฟล์ CA ของคุณ
    pdf_path = 'your_pdf.pdf'  # ไฟล์ PDF ของคุณ

    verified_signers = extract_certificates(pdf_path, cert_path)
    print("ชื่อผู้เซ็นที่ผ่านการตรวจสอบ:", verified_signers)
'''
