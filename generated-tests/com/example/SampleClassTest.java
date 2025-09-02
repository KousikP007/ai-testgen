package com.example;

import org.junit.Before;
import org.junit.Test;
import static org.junit.Assert.*;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import static org.mockito.Mockito.*;

public class SampleClassTest {
    @Before
    public void setup() { MockitoAnnotations.openMocks(this); }

    @Test
        public void testAdd() throws Exception {
            // Set up mocks
            SampleClass sampleClass = Mockito.mock(SampleClass.class);
            // Set up input values
            int a=10, b=5;
            // Call the method to be tested
            sampleClass.add(a,b);
            // Verify behavior
            Mockito.verify(sampleClass).add(Mockito.eq(a), Mockito.eq(b));
        }
    }
    @Test
         public void testConcat_withValidInputs_shouldReturnValidString(){
             String a = "hello";
             String b = "world";
             
             sampleClass.concat(a,b);
             
             Assert.assertEquals("helloworld",sampleClass.getResult());
         } 
    }
    @Test
        public void test_hiddenMethod() throws Exception {
            // Arrange
            PowerMockito.mockStatic(SampleClass.class);
            // Act
            sampleClass.hidden("abc");
            // Assert
            Mockito.verifyPrivate(sampleClass).invoke("hidden", "abc");
        }
    }
}
