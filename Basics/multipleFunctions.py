class consolidated:
    def Subfields(self):  
        subfields = ["Machine Learning",
"Neural Networks",
"Vision",
"Robotics",
"Speech Processing",
"Natural Language Processing"]
        print("Sub-fields in AI are:")
        for fields in subfields:
            print(fields)


    def OddEven(self):
        num = int(input("Enter a number"))
        if(num%2==0):
            print(str(num)+ " is Even number")
        else:
            print(str(num)+ " is Odd number")


    def Elegible(self,gender,age):
        if(gender.lower() =="male"):
            if int(age) >= 21:
                print("Eligible for marriage.")
            else:
                print("Not eligible for marriage.")
        elif gender.lower() == "female":
            if int(age) >= 18:
                print("Eligible for marriage.")
            else:
                print("Not eligible for marriage.")


    def percentage(self,sub1,sub2,sub3,sub4,sub5):
        total_marks  = sub1+sub2+sub3+sub4+sub5
        percent = (total_marks/500)*100
        print("Percentage "+str(percent))


    def trianglearea(self,height,breadth):

        area = (height*breadth)/2
        print("Area of triangle "+str(area))

    
    def triangeperimeter(self,height1,height2,breadth):

        perimiter = height1+height2+breadth
        print("perimter of triangle "+str(perimiter))