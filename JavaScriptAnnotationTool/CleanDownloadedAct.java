import java.io.*;
import java.util.*;
import org.jdom2.*;
import org.jdom2.output.*;
import org.jdom2.input.*;
import java.nio.charset.*;

public class CleanDownloadedAct 
{
   
    /**
    private static File inputFile = new File("C:/D/NLP/Papers in Progress/Kuuku/SPIN internship 2023-2024/GOLD STANDARD/Police, Crime, Sentencing and Courts Act 2022/JavaScriptAnnotationTool/"
            + "ORIGINAL_Police, Crime, Sentencing and Courts Act 2022 (c. 32).xhtml");
    
    private static File outputFile = new File("C:/D/NLP/Papers in Progress/Kuuku/SPIN internship 2023-2024/GOLD STANDARD/Police, Crime, Sentencing and Courts Act 2022/JavaScriptAnnotationTool/"
            + "Police, Crime, Sentencing and Courts Act 2022 (c. 32).xhtml");
    /**/
    
    /**/

  
    /**/
    public static void main(String[] args)
    {
        if(args.length == 2)
        {
            processFile(args[0], args[1]);
        }
        else
        {
            
            // Fallback to default file paths if arguments are not provided.
            File folder = new File("./input/");
            File[] listOfFiles = folder.listFiles((dir, name) -> name.toLowerCase().endsWith(".xhtml"));

            if (listOfFiles != null) {
                for (File file : listOfFiles) {
                    if (file.isFile()) {
                        String inputFilePath = file.getAbsolutePath();
                        String outputFilePath = "./output_folder/" + file.getName();
                        processFile(inputFilePath, outputFilePath);
                    }
                }
            } else {
                System.out.println("The folder is empty or does not exist.");
            }

            //processFile("./1985_49.xhtml", "./1985_49processed.xhtml"); 
        }
    }
    
    public static void processFile(String inputFilePath, String outputFilePath) 
    {        
        try 
        {
            // Create File objects using the provided paths
            File inputFile = new File(inputFilePath);
            File outputFile = new File(outputFilePath);

            BufferedReader in = new BufferedReader(new FileReader(inputFile));
            String text = "";
            String buffer = "";
            while((buffer=in.readLine())!=null)text=text+buffer;
            text=removeUndesiredText(text);
            
            Document doc = (Document)new SAXBuilder().build(new ByteArrayInputStream(text.getBytes(StandardCharsets.UTF_8)));
            doc.getRootElement().addNamespaceDeclaration(Namespace.getNamespace("xsi", "http://www.w3.org/2001/XMLSchema-instance"));
            
               // ***** INSERT SCRIPT CODE INTO THE <head> ELEMENT *****
            Namespace ns = doc.getRootElement().getNamespace();
            Element head = doc.getRootElement().getChild("head", ns);
            
            // ***** END SCRIPT INSERTION *****

            removeUndesiredElements(doc.getRootElement());
            removeSpanIncludingOnlyTextMustBeRemoved(doc.getRootElement());
            removeDoubleRemovedTextElements(doc.getRootElement());
                //we do it twice because the merging (removeDoubleRemovedTextElements) might create a span with a single Text.
            removeSpanIncludingOnlyTextMustBeRemoved(doc.getRootElement());
            removeDoubleRemovedTextElements(doc.getRootElement());
            
            while(outputFile.exists())outputFile.delete();
            XMLOutputter outputter = new XMLOutputter();
            outputter.setFormat(Format.getPrettyFormat().setEncoding("UTF-8"));
            FileOutputStream fos = new FileOutputStream(outputFile);
            OutputStreamWriter osw = new OutputStreamWriter(fos, "UTF8");
            outputter.output(doc, osw);
            osw.close();
            fos.close();
        }
        catch(Exception e)
        {
            System.out.println(e.getClass().getName()+": "+e.getMessage());
        }
    }
    
    private static String removeUndesiredText(String text)
    {
        //if(text==text)return text;
        //System.out.println(text);
        
        String DOCTYPE = "\"http://www.w3.org/MarkUp/DTD/xhtml-rdfa-1.dtd\">";
        text = text.substring(text.indexOf(DOCTYPE)+DOCTYPE.length(),text.length());
        
        while(text.indexOf("/styles/")!=-1)
        {
            text = text.substring(0, text.indexOf("/styles/"))+
                "styles/"+
                text.substring(text.indexOf("/styles/")+"/styles/".length(),text.length());
        }
        
        return text;
    }
    
    private static void removeUndesiredElements(Element e)
    {
        //if(e==e)return;
        
        boolean remove=false;
        boolean removesubsequents=false;
        
            //remove the "[" and the "]"
        if
        (
            (e.getName().compareToIgnoreCase("span")==0)&&
            (e.getAttributeValue("class")!=null)&&
            (e.getAttributeValue("class").compareToIgnoreCase("LegChangeDelimiter")==0)
        )remove=true;
            //remove the "F*" after the "["
        if
        (
            (e.getName().compareToIgnoreCase("a")==0)&&
            (e.getAttributeValue("class")!=null)&&
            (e.getAttributeValue("class").compareToIgnoreCase("LegCommentaryLink")==0)
        )remove=true;
            //remove la tabella con le passive modifications (o come si chiamano, la tabella associata alla "[F*...]").
        if
        (
            (e.getName().compareToIgnoreCase("div")==0)&&
            (e.getAttributeValue("class")!=null)&&
            (e.getAttributeValue("class").compareToIgnoreCase("LegAnnotations")==0)
        )remove=true;
            //remove all schedules (LegSchedulesTitle è dove sta il titolo SCHEDULES)
            //Quando individuo uno schedule devo cancellare tutti gli elements successivi nello stesso <div>,
            //ecco perchè c'è removesubsequents=true.
        if
        (
            (e.getName().compareToIgnoreCase("h1")==0)&&
            (e.getAttributeValue("class")!=null)&&
            (e.getAttributeValue("class").compareToIgnoreCase("LegSchedulesTitle")==0)
        ){remove=true;removesubsequents=true;}
        
            //The method removeOtherActsAmendments search if "e" denotes an amendment, in which case we will
            //replace e (and all subsequent elements) with the Element returned by the method.            
        Text replaceT=removeOtherActsAmendments(e);
        
        if(remove==true)
        {
            Element parent = e.getParentElement();
                //Quando removesubsequents=true, vengono rimossi Element(s) che poi magari vengono richiamati nelle next 
                //iterations dalla procedura chiamante. Ma il loro parent è adesso null, perchè sono stati rimossi.
            if(parent==null)return;
            int index = parent.getContent().indexOf(e);
            parent.getContent().remove(e);
            
            while((removesubsequents==true)&&(index<parent.getContent().size()))parent.getContent().remove(index);
        }
            //If this is not null, "e" must be emptied and replaceE must be its sole content 
            //(replaceE contains a dummy message, e.g., "DO NOT ANNOTATE THIS TEXT")
        else if(replaceT!=null)
        {
            e.getContent().clear();
            e.getContent().add(replaceT);
            e.setAttribute("style", "color:red;font-weight:bold");
        }
        else
        {
            ArrayList<Element> elements = new ArrayList<Element>();
            for(Element se:e.getChildren())elements.add(se);
            for(Element se:elements)removeUndesiredElements(se);
        }
    }
    
        //Some norms contains amendments to other acts. These amendments can in turn be norms. 
        //E.g., "The act XXX is modified as follows: in section 3 insert— 'The person must etc...."
        //The Element with the keyword to modify (e.g., "insert—") is removed, together with all Element(s) that come after it 
        //in the same <div>. The Element returned by this method is then inserted in its place. If the Element in input does
        //not contain a keyword that denotes an amendment, this method returns null.
    private static Text removeOtherActsAmendments(Element e)
    {
        //if(e==e)return null;
        
        String classAttribute = e.getAttributeValue("class");
        if(classAttribute==null)return null;
        if
        (
            (classAttribute.compareToIgnoreCase("LegClearFix LegP2Container LegAmend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegClearFix LegP3Container LegAmend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegClearFix LegP4Container LegAmend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegRHS LegP1TextC1Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegRHS LegP2TextC1Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegRHS LegP3TextC1Amend")!=0)    
            &&(classAttribute.compareToIgnoreCase("LegTabbedDefC1Amend LegUnorderedListC1Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegPartNo LegC1Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegSP1GroupTitleFirstC1Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegClearFix LegSP1Container LegAmend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegClearFix LegSP2Container LegAmend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegClearFix LegSP3Container LegAmend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegSP1GroupTitleC1Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegPartTitle LegC1Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegTabbedDefC3Amend LegUnorderedListC3Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegDS LegP1NoC3Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegDS LegRHS LegP1TextC3Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegSP1GroupTitleFirstC3Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegChapterNo LegC1Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegChapterTitle LegC1Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegRHS LegP2TextC3Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegClearFix LegSP4Container LegAmend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegTextC1Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegDS LegP1GroupTitleFirstC1Amend")!=0)
            &&(classAttribute.compareToIgnoreCase("LegDS LegP1NoC1Amend")!=0)
        )return null;
                                               
            //This is the text we'll put in place of the one that we remove, for the annotator to understand that it is hidden.
        return new Text("TEXT REMOVED. MUST NOT BE ANNOTATED");
    }
    
    private static void removeSpanIncludingOnlyTextMustBeRemoved(Element e)
    {
        if
        ( 
            (e.getName().compareToIgnoreCase("span")!=0)||
            (e.getContent().size()!=1)||
            (!(e.getContent().get(0)instanceof Text))
        )
        {
            ArrayList<Element> elements = new ArrayList<Element>();
            for(Element se:e.getChildren())elements.add(se);
            for(Element se:elements)removeSpanIncludingOnlyTextMustBeRemoved(se);
            return;
        }
        
        if(((Text)e.getContent().get(0)).getText().compareToIgnoreCase("TEXT REMOVED. MUST NOT BE ANNOTATED")==0)
        {
            Element parent = e.getParentElement();
            if(parent.getContent().size()!=1)return;
            parent.getContent().clear();
            parent.addContent(new Text("TEXT REMOVED. MUST NOT BE ANNOTATED"));
            parent.setAttribute("style", "color:red;font-weight:bold");
        }
        
    }
    
    private static void removeDoubleRemovedTextElements(Element e)
    {
        //if(e==e)return;
        
        if((e.getAttributeValue("style")!=null)&&(e.getAttributeValue("style").compareToIgnoreCase("color:red;font-weight:bold")==0))
        {
            if(e.getParentElement()==null)return;//se vale questo, è perchè "e" è già stato rimosso in una precedente ricorsione.
            
            Element parent = e.getParentElement();
            int index = parent.getChildren().indexOf(e);
            
            if(index>0)
            {
                    //Se quello prima anche è rosso, allora togliamo questo.
                if
                (
                    (parent.getChildren().get(index-1).getAttributeValue("style")!=null)&&
                    (parent.getChildren().get(index-1).getAttributeValue("style").compareToIgnoreCase("color:red;font-weight:bold")==0)
                )parent.getChildren().remove(index);
                    //Sennò, in caso questo element abbia l'attributo "class", lo togliamo. Questo mi printerà tutti i messaggi
                    //sulla sinistra (tutti uguali, invece con class me li potrebbe allineare in modo diverso).
                else if(e.getAttributeValue("class")!=null)e.removeAttribute("class");
            }
        }
        else
        {
            ArrayList<Element> elements = new ArrayList<Element>();
            for(Element se:e.getChildren())elements.add(se);
            for(Element se:elements)removeDoubleRemovedTextElements(se);
        }
    }
}